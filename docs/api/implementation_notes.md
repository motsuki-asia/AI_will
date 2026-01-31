# AI will API - 実装ノート

| 項目 | 内容 |
|------|------|
| ドキュメント名 | API実装ノート |
| 作成日 | 2026-01-31 |
| 対象 | FastAPI バックエンドスケルトン |

---

## 目次

1. [ディレクトリ構造](#1-ディレクトリ構造)
2. [起動手順](#2-起動手順)
3. [開発環境セットアップ](#3-開発環境セットアップ)
4. [アーキテクチャ概要](#4-アーキテクチャ概要)
5. [実装ステータス](#5-実装ステータス)
6. [次のステップ](#6-次のステップ)
7. [OpenAPI Lint 実行手順](#7-openapi-lint-実行手順)
8. [Auth API 疎通確認手順](#8-auth-api-疎通確認手順)

---

## 1. ディレクトリ構造

```
app/
├── __init__.py
├── main.py                 # FastAPI アプリケーションエントリポイント
├── deps.py                 # 依存性注入（認証、ページング等）
│
├── api/
│   ├── __init__.py
│   └── v1/
│       ├── __init__.py
│       └── routers/
│           ├── __init__.py
│           ├── auth.py         # 認証・ユーザー管理
│           ├── catalog.py      # Pack検索・閲覧
│           ├── conversation.py # 会話機能
│           ├── purchase.py     # 購入・復元
│           ├── memory.py       # メモリー（クリップ）
│           ├── safety.py       # 通報・ブロック
│           └── privacy.py      # プライバシー設定
│
├── schemas/
│   ├── __init__.py
│   ├── common.py           # 共通スキーマ（Pagination, Error等）
│   ├── auth.py             # 認証関連スキーマ
│   ├── catalog.py          # カタログ関連スキーマ
│   ├── conversation.py     # 会話関連スキーマ
│   ├── purchase.py         # 購入関連スキーマ
│   ├── memory.py           # メモリー関連スキーマ
│   ├── safety.py           # 安全機能関連スキーマ
│   └── privacy.py          # プライバシー関連スキーマ
│
└── core/
    ├── __init__.py
    ├── config.py           # 設定管理（環境変数）
    ├── security.py         # JWT認証、パスワードハッシュ
    └── errors.py           # 統一エラーハンドリング
```

---

## 2. 起動手順

### 2.1 前提条件

- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### 2.2 セットアップ

```bash
# 1. 仮想環境の作成
python -m venv venv

# 2. 仮想環境の有効化
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 3. 依存関係のインストール
pip install -r requirements.txt
```

### 2.3 環境変数の設定

`.env` ファイルをプロジェクトルートに作成:

```env
# Application
APP_NAME="AI will API"
DEBUG=true

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/aiwill

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# LLM Provider
LLM_PROVIDER=openai
LLM_API_KEY=your-openai-api-key
LLM_TIMEOUT_SECONDS=30
```

### 2.4 サーバー起動

```bash
# 開発モード（ホットリロード有効）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# または
python -m app.main
```

### 2.5 動作確認

```bash
# ヘルスチェック
curl http://localhost:8000/health

# OpenAPI ドキュメント（DEBUG=true の場合）
open http://localhost:8000/docs
```

---

## 3. 開発環境セットアップ

### 3.1 コードフォーマット

```bash
# Black でフォーマット
black app/

# isort でインポート整理
isort app/
```

### 3.2 リント

```bash
# Flake8
flake8 app/

# MyPy（型チェック）
mypy app/
```

### 3.3 テスト

```bash
# テスト実行
pytest

# カバレッジ付き
pytest --cov=app --cov-report=html
```

---

## 4. アーキテクチャ概要

### 4.1 レイヤー構造

```
Request
   ↓
[Router] - パス/メソッドのルーティング、バリデーション
   ↓
[Dependencies] - 認証、ページング、共通パラメータ
   ↓
[Service] - ビジネスロジック（TODO: 実装）
   ↓
[Repository] - データアクセス（TODO: 実装）
   ↓
[Database]
```

### 4.2 認証フロー

```
1. POST /v1/auth/login
   → ユーザー認証
   → JWT access_token + refresh_token 発行

2. 保護されたエンドポイント
   → Authorization: Bearer {access_token}
   → deps.get_current_user_id で検証
   → deps.require_onboarding_completed で状態確認

3. トークン更新
   → POST /v1/auth/refresh
   → refresh_token で新しい access_token を取得
```

### 4.3 エラーハンドリング

すべてのエラーは `rules/api.mdc` に準拠した統一フォーマット:

```json
{
  "error": {
    "code": "error_code",
    "message": "エラーメッセージ",
    "details": [
      {
        "field": "フィールド名",
        "code": "エラーコード",
        "message": "詳細メッセージ"
      }
    ]
  }
}
```

`app/core/errors.py` で定義された例外クラスを使用:

```python
from app.core.errors import NotFoundException, ForbiddenException

# 404
raise NotFoundException("Pack が見つかりません")

# 403 (カスタムコード)
raise ForbiddenException(
    message="このコンテンツは年齢制限があります",
    code=ErrorCode.AGE_RESTRICTED
)
```

---

## 5. 実装ステータス

### 5.1 完了済み

| カテゴリ | 内容 | ファイル |
|---------|------|---------|
| ✅ | アプリケーション設定 | `core/config.py` |
| ✅ | JWT認証基盤 | `core/security.py` |
| ✅ | 統一エラー形式 | `core/errors.py` |
| ✅ | 依存性注入 | `deps.py` |
| ✅ | Pydantic スキーマ | `schemas/*.py` |
| ✅ | API ルーター | `api/v1/routers/*.py` |
| ✅ | **SQLAlchemy モデル** | `models/user.py`, `models/refresh_token.py` |
| ✅ | **Alembic マイグレーション** | `alembic/` |
| ✅ | **Auth 完全実装** | `services/auth.py`, `api/v1/routers/auth.py` |

### 5.2 Auth エンドポイント（本実装済み）

| エンドポイント | ステータス | 備考 |
|---------------|-----------|------|
| `POST /v1/auth/register` | ✅ 完了 | ユーザー登録 + JWT発行 |
| `POST /v1/auth/login` | ✅ 完了 | ログイン + JWT発行 |
| `POST /v1/auth/refresh` | ✅ 完了 | トークンローテーション対応 |
| `POST /v1/auth/logout` | ✅ 完了 | refresh_token 無効化 |
| `GET /v1/me` | ✅ 完了 | ユーザー情報 + オンボーディング状態 |
| `PATCH /v1/me` | ✅ 完了 | display_name 更新 |
| `POST /v1/me/consent` | 🚧 Phase 2 | 利用規約同意 |
| `POST /v1/me/age-verify` | 🚧 Phase 2 | 年齢確認 |

### 5.3 TODO（実装が必要）

| 優先度 | カテゴリ | 内容 |
|-------|---------|------|
| **P0** | Conversation | メッセージ送信（LLM連携） |
| **P1** | Catalog | Pack 検索・詳細 |
| **P1** | Cache | Redis キャッシュ |
| **P1** | Idempotency | 冪等性キー管理 |
| **P2** | Rate Limiting | レート制限ミドルウェア |
| **P2** | Logging | 構造化ログ |
| **P2** | Monitoring | メトリクス収集 |

---

## 6. 次のステップ

### 6.1 データベース層の実装

```
app/
├── models/
│   ├── __init__.py
│   ├── base.py           # Base, TimestampMixin
│   ├── user.py           # User, TermsAgreement
│   ├── pack.py           # Pack, PackItem, PackTag
│   ├── character.py      # Character
│   ├── conversation.py   # ConversationSession, ConversationMessage
│   ├── memory.py         # MemoryClip
│   ├── purchase.py       # Purchase, Entitlement
│   └── safety.py         # Report, Block
│
├── repositories/
│   ├── __init__.py
│   ├── base.py           # BaseRepository
│   ├── user.py
│   └── ...
│
└── services/
    ├── __init__.py
    ├── auth.py
    ├── conversation.py
    └── ...
```

### 6.2 LLM 連携の実装

```python
# app/services/llm/base.py
class LLMProvider(Protocol):
    async def generate(
        self,
        messages: List[Dict],
        character: Character,
        stream: bool = False,
    ) -> AsyncIterator[str]:
        ...

# app/services/llm/openai.py
class OpenAIProvider(LLMProvider):
    ...
```

### 6.3 テストの追加

```
tests/
├── conftest.py           # pytest fixtures
├── test_auth.py
├── test_catalog.py
├── test_conversation.py
└── ...
```

---

## 7. OpenAPI Lint 実行手順

### 7.1 事前準備

```bash
# 必要なパッケージをインストール
pip install pyyaml openapi-spec-validator

# （オプション）より厳密な lint には Spectral を使用
npm install -g @stoplight/spectral-cli
```

### 7.2 基本的な検証

```bash
# Python スクリプトで検証（推奨）
python scripts/validate_openapi.py

# 出力例:
# Validating: docs/api/openapi.yaml
# --------------------------------------------------
# [OK] OpenAPI 3.1 structure is valid
# [OK] All $ref references are valid
# [OK] All operationIds are unique
# --------------------------------------------------
# Stats: 36 endpoints, 73 schemas
#
# [SUCCESS] OpenAPI spec is valid!
```

### 7.3 検証スクリプトの機能

`scripts/validate_openapi.py` は以下を検証します:

| 検証項目 | 説明 |
|---------|------|
| OpenAPI 3.1 構造 | `openapi-spec-validator` による仕様準拠チェック |
| $ref 参照 | すべての `$ref` が正しく解決できるか |
| operationId 重複 | `operationId` が一意であるか |
| 統計情報 | エンドポイント数、スキーマ数の表示 |

### 7.4 Spectral による追加 lint（オプション）

```bash
# Spectral CLI で lint（npm が必要）
npx @stoplight/spectral-cli lint docs/api/openapi.yaml

# カスタムルールセットを使用する場合
# .spectral.yaml をプロジェクトルートに配置
npx @stoplight/spectral-cli lint docs/api/openapi.yaml --ruleset .spectral.yaml
```

### 7.5 CI/CD での検証

```yaml
# GitHub Actions 例
- name: Validate OpenAPI
  run: |
    pip install openapi-spec-validator pyyaml
    python scripts/validate_openapi.py
```

### 7.6 よくあるエラーと対処

| エラー | 原因 | 対処 |
|-------|------|------|
| `Broken $ref: #/components/schemas/Xxx` | 参照先スキーマが存在しない | スキーマを追加するか、$ref を修正 |
| `Duplicate operationId: xxx` | 同じ operationId が複数定義されている | ユニークな operationId に変更 |
| `Invalid type` | 型定義が不正 | `string`, `integer`, `object` 等の有効な型に修正 |

---

## 8. Auth API 疎通確認手順

### 8.1 サーバー起動

```bash
# 1. 仮想環境を有効化
source venv/Scripts/activate  # Windows (Git Bash)
# または
venv\Scripts\activate  # Windows (cmd)

# 2. 依存関係インストール（初回のみ）
pip install -r requirements.txt

# 3. マイグレーション実行
alembic upgrade head

# 4. サーバー起動
uvicorn app.main:app --reload --port 8000
```

### 8.2 curl による疎通確認

```bash
# ヘルスチェック
curl http://localhost:8000/health

# === 1. ユーザー登録 ===
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecureP@ss123"}'

# 出力例:
# {
#   "user": {"id": "xxx", "email": "test@example.com", ...},
#   "tokens": {"access_token": "eyJ...", "refresh_token": "eyJ...", "expires_in": 3600}
# }

# === 2. ログイン ===
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecureP@ss123"}'

# === 3. ユーザー情報取得（要認証） ===
ACCESS_TOKEN="eyJ..."  # ログインで取得した access_token
curl http://localhost:8000/v1/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# === 4. プロフィール更新（要認証） ===
curl -X PATCH http://localhost:8000/v1/me \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"display_name":"Test User"}'

# === 5. トークン更新 ===
REFRESH_TOKEN="eyJ..."  # ログインで取得した refresh_token
curl -X POST http://localhost:8000/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}"

# === 6. ログアウト（要認証） ===
curl -X POST http://localhost:8000/v1/auth/logout \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
# → HTTP 204 No Content
```

### 8.3 エラーケースの確認

```bash
# 重複登録（409 Conflict）
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecureP@ss123"}'

# 認証失敗（401 Unauthorized）
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"wrongpassword"}'

# 認証なしでアクセス（401 Unauthorized）
curl http://localhost:8000/v1/me
```

### 8.4 OpenAPI ドキュメント（Swagger UI）

```
http://localhost:8000/docs
```

DEBUG=true の場合、上記 URL で Swagger UI が利用可能です。

---

## 参照ドキュメント

- [docs/api/openapi.yaml](./openapi.yaml) - OpenAPI 仕様書
- [docs/api/api.md](./api.md) - API 設計書
- [rules/api.mdc](../../rules/api.mdc) - API 設計規約
- [database_design.md](../../database_design.md) - テーブル設計書
- [scripts/validate_openapi.py](../../scripts/validate_openapi.py) - OpenAPI 検証スクリプト
