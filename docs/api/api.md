# AI will API 設計書

| 項目 | 内容 |
|------|------|
| ドキュメント名 | AI will API 設計書 |
| バージョン | 1.2.0 |
| 作成日 | 2026-01-31 |
| 最終更新日 | 2026-01-31 |
| 規約参照 | [rules/api.mdc](../../rules/api.mdc) |
| 対象範囲 | MVP（Phase 1） |

---

## 目次

1. [概要](#1-概要)
2. [共通仕様](#2-共通仕様)
3. [Auth - 認証・ユーザー管理](#3-auth---認証ユーザー管理)
4. [Catalog - Pack 検索・閲覧](#4-catalog---pack-検索閲覧)
5. [Conversation - 会話](#5-conversation---会話)
6. [Safety - 通報](#6-safety---通報)
7. [Privacy - 会話履歴削除](#7-privacy---会話履歴削除)
8. [Open Questions](#8-open-questions)

---

## 1. 概要

### 1.1 MVP 対象ユーザーストーリー

| ID | ストーリー | API 章 |
|----|-----------|--------|
| EU-001 | アカウント登録（メール+パスワード） | [3. Auth](#3-auth---認証ユーザー管理) |
| EU-002 | 年齢確認と年齢に応じた制限 | [3. Auth](#3-auth---認証ユーザー管理) |
| EU-003a | Persona/Scenario の一覧＋詳細 | [4. Catalog](#4-catalog---pack-検索閲覧) |
| EU-005 | テキスト会話＋保存＋再開＋タイムアウトUX | [5. Conversation](#5-conversation---会話) |
| EU-007 | 通報（基本） | [6. Safety](#6-safety---通報) |
| EU-008 | 会話履歴削除 | [7. Privacy](#7-privacy---会話履歴削除) |

### 1.2 ベース URL

```
https://api.aiwill.app/v1
```

---

## 2. 共通仕様

### 2.1 認証

| 項目 | 仕様 |
|------|------|
| 方式 | JWT Bearer Token |
| ヘッダー | `Authorization: Bearer {access_token}` |

### 2.2 エラーレスポンス

```json
{
  "error": {
    "code": "error_code",
    "message": "人間向けメッセージ",
    "details": []
  }
}
```

### 2.3 ページング

| パラメータ | 型 | 説明 | デフォルト |
|-----------|-----|------|-----------|
| `cursor` | string | カーソル | — |
| `limit` | integer | 取得件数（1〜100） | 20 |

**レスポンス:**

```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "...",
    "has_more": true
  }
}
```

### 2.4 共通エラーコード

| HTTP | code | 説明 |
|------|------|------|
| 400 | `validation_error` | パラメータ不正 |
| 401 | `unauthenticated` | 認証が必要 |
| 401 | `token_expired` | トークン期限切れ |
| 403 | `forbidden` | 権限不足 |
| 403 | `age_restricted` | 年齢制限 |
| 404 | `not_found` | リソースなし |
| 429 | `rate_limit_exceeded` | レート制限 |
| 500 | `internal_error` | サーバーエラー |

---

## 3. Auth - 認証・ユーザー管理

### 対象ストーリー

- **EU-001**: アカウント登録（メール+パスワード、利用規約同意）
- **EU-002**: 年齢確認と年齢に応じた制限

### 対象画面

- S-001: ログイン
- S-002: 登録
- S-003: 同意画面
- S-010: 年齢確認
- S-000: 起動/初期ロード

---

### 3.1 POST /v1/auth/register

**目的:** 新規ユーザー登録（EU-001 / S-002）

#### Auth

| 認証 | 権限 |
|------|------|
| 不要 | — |

#### Request

```http
POST /v1/auth/register
Content-Type: application/json
```

```json
{
  "email": "user@example.com",
  "password": "SecureP@ss123"
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `email` | string | ✓ | メールアドレス（RFC 5322準拠） |
| `password` | string | ✓ | パスワード（8文字以上、大小英数記号含む） |

#### Response

**201 Created**

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "consent_at": null,
    "age_verified_at": null,
    "age_group": null,
    "created_at": "2026-01-31T12:00:00Z"
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2g...",
    "expires_in": 3600
  }
}
```

#### エラー

| HTTP | code | 条件 |
|------|------|------|
| 400 | `validation_error` | メール形式不正、パスワード要件未達 |
| 409 | `conflict` | メールアドレス重複 |

#### DB 対応

| テーブル | 操作 |
|---------|------|
| `users` | INSERT |

---

### 3.2 POST /v1/auth/login

**目的:** ログイン（EU-001 / S-001）

#### Auth

| 認証 | 権限 |
|------|------|
| 不要 | — |

#### Request

```http
POST /v1/auth/login
Content-Type: application/json
```

```json
{
  "email": "user@example.com",
  "password": "SecureP@ss123"
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `email` | string | ✓ | メールアドレス |
| `password` | string | ✓ | パスワード |

#### Response

**200 OK**

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "consent_at": "2026-01-31T12:00:00Z",
    "age_verified_at": "2026-01-31T12:05:00Z",
    "age_group": "adult",
    "created_at": "2026-01-31T12:00:00Z"
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2g...",
    "expires_in": 3600
  }
}
```

#### エラー

| HTTP | code | 条件 |
|------|------|------|
| 400 | `validation_error` | パラメータ不正 |
| 401 | `invalid_credentials` | メール/パスワード不一致 |
| 423 | `account_locked` | アカウントロック（連続失敗） |

#### DB 対応

| テーブル | 操作 |
|---------|------|
| `users` | SELECT |
| `audit_logs` | INSERT（ログイン記録） |

---

### 3.3 POST /v1/auth/refresh

**目的:** アクセストークン更新

#### Auth

| 認証 | 権限 |
|------|------|
| 不要（refresh_token 使用） | — |

#### Request

```http
POST /v1/auth/refresh
Content-Type: application/json
```

```json
{
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2g..."
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `refresh_token` | string | ✓ | リフレッシュトークン |

#### Response

**200 OK**

```json
{
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "bmV3IHJlZnJlc2ggdG9rZW4...",
    "expires_in": 3600
  }
}
```

#### エラー

| HTTP | code | 条件 |
|------|------|------|
| 401 | `invalid_refresh_token` | トークン無効/期限切れ |

#### DB 対応

| テーブル | 操作 |
|---------|------|
| — | トークン検証（JWT / Redis） |

---

### 3.4 POST /v1/auth/logout

**目的:** ログアウト（リフレッシュトークン無効化）

#### Auth

| 認証 | 権限 |
|------|------|
| 必須 | — |

#### Request

```http
POST /v1/auth/logout
Authorization: Bearer {access_token}
Content-Type: application/json
```

```json
{
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2g..."
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `refresh_token` | string | — | 無効化対象（省略時は全セッション） |

#### Response

**204 No Content**

#### DB 対応

| テーブル | 操作 |
|---------|------|
| — | トークン無効化（Redis / DB） |
| `audit_logs` | INSERT（ログアウト記録） |

---

### 3.5 GET /v1/me

**目的:** 認証ユーザー情報取得（S-000 状態判定）

#### Auth

| 認証 | 権限 |
|------|------|
| 必須 | — |

#### Request

```http
GET /v1/me
Authorization: Bearer {access_token}
```

#### Response

**200 OK**

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "display_name": "ユーザー名",
    "consent_at": "2026-01-31T12:00:00Z",
    "age_verified_at": "2026-01-31T12:05:00Z",
    "age_group": "adult",
    "created_at": "2026-01-31T12:00:00Z",
    "updated_at": "2026-01-31T12:10:00Z"
  },
  "onboarding": {
    "consent_completed": true,
    "age_verified": true,
    "completed": true
  }
}
```

**onboarding フラグ:**

| フラグ | 説明 |
|--------|------|
| `consent_completed` | 利用規約同意済み |
| `age_verified` | 年齢確認済み |
| `completed` | オンボーディング完了 |

#### エラー

| HTTP | code | 条件 |
|------|------|------|
| 401 | `unauthenticated` | 未認証 |
| 401 | `token_expired` | トークン期限切れ |

#### DB 対応

| テーブル | 操作 |
|---------|------|
| `users` | SELECT |

---

### 3.6 POST /v1/me/consent

**目的:** 利用規約・プライバシーポリシー同意（EU-001 / S-003）

#### Auth

| 認証 | 権限 |
|------|------|
| 必須 | — |

#### Request

```http
POST /v1/me/consent
Authorization: Bearer {access_token}
Content-Type: application/json
```

```json
{
  "terms_version": "1.0.0",
  "privacy_version": "1.0.0"
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `terms_version` | string | ✓ | 同意した利用規約バージョン |
| `privacy_version` | string | ✓ | 同意したプライバシーポリシーバージョン |

#### Response

**200 OK**

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "consent_at": "2026-01-31T12:00:00Z"
  },
  "onboarding": {
    "consent_completed": true,
    "age_verified": false,
    "completed": false
  }
}
```

#### エラー

| HTTP | code | 条件 |
|------|------|------|
| 400 | `validation_error` | バージョン不正 |
| 409 | `already_consented` | 同意済み（同一バージョン） |

#### DB 対応

| テーブル | 操作 |
|---------|------|
| `users` | UPDATE（consent_at） |
| `terms_agreements` | INSERT |

---

### 3.7 POST /v1/me/age-verify

**目的:** 年齢確認（EU-002 / S-010）

#### Auth

| 認証 | 権限 |
|------|------|
| 必須 | 同意完了 |

#### Request

```http
POST /v1/me/age-verify
Authorization: Bearer {access_token}
Content-Type: application/json
```

```json
{
  "birth_date": "1990-01-15"
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `birth_date` | string (date) | ✓ | 生年月日（YYYY-MM-DD） |

**代替リクエスト（年齢帯選択）:**

```json
{
  "age_group": "adult"
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `age_group` | string | ✓ | 年齢区分（`u13`, `u18`, `adult`） |

#### Response

**200 OK**

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "age_verified_at": "2026-01-31T12:05:00Z",
    "age_group": "adult"
  },
  "onboarding": {
    "consent_completed": true,
    "age_verified": true,
    "completed": true
  },
  "restrictions": {
    "adult_content": true,
    "purchase_limit": null
  }
}
```

**restrictions:**

| フィールド | 説明 |
|-----------|------|
| `adult_content` | 成人向けコンテンツ閲覧可 |
| `purchase_limit` | 課金上限（円/月、null=制限なし） |

#### エラー

| HTTP | code | 条件 |
|------|------|------|
| 400 | `validation_error` | 日付形式不正 |
| 403 | `consent_required` | 同意未完了 |
| 409 | `already_verified` | 年齢確認済み |

#### DB 対応

| テーブル | 操作 |
|---------|------|
| `users` | UPDATE（age_verified_at, age_group） |
| `audit_logs` | INSERT（年齢確認記録） |

---

### 3.8 PATCH /v1/me

**目的:** プロフィール更新

#### Auth

| 認証 | 権限 |
|------|------|
| 必須 | オンボーディング完了 |

#### Request

```http
PATCH /v1/me
Authorization: Bearer {access_token}
Content-Type: application/json
```

```json
{
  "display_name": "新しい表示名"
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `display_name` | string | — | 表示名（1〜50文字） |

#### Response

**200 OK**

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "display_name": "新しい表示名",
    "updated_at": "2026-01-31T12:15:00Z"
  }
}
```

#### エラー

| HTTP | code | 条件 |
|------|------|------|
| 400 | `validation_error` | 文字数超過等 |

#### DB 対応

| テーブル | 操作 |
|---------|------|
| `users` | UPDATE |

---

## 4. Catalog - Pack 検索・閲覧

### 対象ストーリー

- **EU-003a**: Persona/Scenario の一覧表示、詳細ページで説明・価格等の確認

### 対象画面

- S-020: マーケット一覧
- S-021: 詳細画面

---

### 4.1 GET /v1/packs

**目的:** Pack 一覧取得（EU-003a / S-020）

#### Auth

| 認証 | 権限 |
|------|------|
| 必須 | オンボーディング完了 |

#### Request

```http
GET /v1/packs?type=persona&limit=20&cursor=xxx
Authorization: Bearer {access_token}
```

**クエリパラメータ:**

| パラメータ | 型 | 必須 | 説明 | デフォルト |
|-----------|-----|------|------|-----------|
| `type` | string | — | Pack 種別（`persona`, `scenario`） | 全種別 |
| `query` | string | — | キーワード検索（名前、説明） | — |
| `tags` | string | — | タグ絞り込み（カンマ区切り） | — |
| `age_rating` | string | — | 年齢レーティング（`all`, `r15`, `r18`） | — |
| `sort` | string | — | ソートキー | `created_at` |
| `order` | string | — | 昇順/降順 | `desc` |
| `cursor` | string | — | ページングカーソル | — |
| `limit` | integer | — | 取得件数（1〜100） | 20 |

**年齢制限の自動フィルタ:**

ユーザーの `age_group` に応じて、閲覧可能な `age_rating` が **自動的にフィルタ** される:

| age_group | 閲覧可能な age_rating |
|-----------|---------------------|
| `u13` | `all` のみ |
| `u18` | `all`, `r15` |
| `adult` | すべて |

**ソートキー:**

| sort | 説明 |
|------|------|
| `created_at` | 作成日時 |
| `popularity` | 人気順（※Phase 2 以降） |
| `price` | 価格順 |

#### Response

**200 OK**

```json
{
  "data": [
    {
      "id": "pack_001",
      "pack_type": "persona",
      "name": "桜井 あかり",
      "description": "明るくて元気な幼馴染。いつもあなたのそばにいてくれる。",
      "thumbnail_url": "https://cdn.aiwill.app/packs/pack_001/thumb.jpg",
      "price": 500,
      "is_free": false,
      "age_rating": "all",
      "tags": [
        { "id": "tag_001", "name": "幼馴染" },
        { "id": "tag_002", "name": "明るい" }
      ],
      "creator": {
        "id": "creator_001",
        "display_name": "クリエイター名"
      },
      "stats": {
        "favorite_count": 1234,
        "conversation_count": 5678
      },
      "created_at": "2026-01-15T10:00:00Z"
    }
  ],
  "pagination": {
    "next_cursor": "eyJpZCI6InBhY2tfMDIwIn0",
    "has_more": true
  }
}
```

#### エラー

| HTTP | code | 条件 |
|------|------|------|
| 400 | `validation_error` | パラメータ不正 |
| 403 | `onboarding_required` | オンボーディング未完了 |

#### DB 対応

| テーブル | 操作 |
|---------|------|
| `packs` | SELECT (WHERE deleted_at IS NULL **AND age_rating フィルタ**) |
| `pack_tags` | JOIN |
| `m_tags` | JOIN |
| `creators` | JOIN |
| `users` | SELECT（current_user.age_group で年齢フィルタ条件決定） |

**実装注意（N+1対策）:** タグ情報は JOIN またはサブクエリで一括取得すること。レスポンスのタグは最大10件に制限。

---

### 4.2 GET /v1/packs/{pack_id}

**目的:** Pack 詳細取得（EU-003a / S-021）

#### Auth

| 認証 | 権限 |
|------|------|
| 必須 | オンボーディング完了 |

#### Request

```http
GET /v1/packs/pack_001
Authorization: Bearer {access_token}
```

#### Response

**200 OK**

```json
{
  "pack": {
    "id": "pack_001",
    "pack_type": "persona",
    "name": "桜井 あかり",
    "description": "明るくて元気な幼馴染。いつもあなたのそばにいてくれる。朝は一緒に登校して、放課後は一緒に帰る。そんな日常がずっと続くと思っていた…。",
    "thumbnail_url": "https://cdn.aiwill.app/packs/pack_001/thumb.jpg",
    "cover_url": "https://cdn.aiwill.app/packs/pack_001/cover.jpg",
    "sample_voice_url": "https://cdn.aiwill.app/packs/pack_001/sample.mp3",
    "price": 500,
    "is_free": false,
    "age_rating": "all",
    "tags": [
      { "id": "tag_001", "name": "幼馴染" },
      { "id": "tag_002", "name": "明るい" }
    ],
    "creator": {
      "id": "creator_001",
      "display_name": "クリエイター名",
      "avatar_url": "https://cdn.aiwill.app/creators/creator_001/avatar.jpg"
    },
    "stats": {
      "favorite_count": 1234,
      "conversation_count": 5678,
      "review_count": 89,
      "average_rating": 4.5
    },
    "created_at": "2026-01-15T10:00:00Z",
    "updated_at": "2026-01-20T15:00:00Z"
  },
  "user_status": {
    "owned": false,
    "favorited": false
  }
}
```

**user_status:**

| フィールド | 説明 |
|-----------|------|
| `owned` | 所持済み |
| `favorited` | お気に入り登録済み |

#### エラー

| HTTP | code | 条件 |
|------|------|------|
| 403 | `age_restricted` | 年齢制限コンテンツ（未成年） |
| 404 | `not_found` | Pack が存在しない |

#### DB 対応

| テーブル | 操作 |
|---------|------|
| `packs` | SELECT |
| `pack_tags` | JOIN |
| `m_tags` | JOIN |
| `creators` | JOIN |
| `user_entitlements` | SELECT（所持確認） |
| `user_favorites` | SELECT（お気に入り確認） |

---

### 4.3 GET /v1/packs/{pack_id}/items

**目的:** Pack 構成アイテム取得

#### Auth

| 認証 | 権限 |
|------|------|
| 必須 | オンボーディング完了 |

#### Request

```http
GET /v1/packs/pack_001/items
Authorization: Bearer {access_token}
```

#### Response

**200 OK**

```json
{
  "data": [
    {
      "id": "item_001",
      "item_type": "character",
      "item_id": "char_001",
      "name": "桜井 あかり",
      "description": "Pack のメインキャラクター"
    },
    {
      "id": "item_002",
      "item_type": "event",
      "item_id": "event_001",
      "name": "初めての告白",
      "description": "好感度が一定以上で解放されるイベント"
    }
  ]
}
```

#### DB 対応

| テーブル | 操作 |
|---------|------|
| `pack_items` | SELECT |
| `characters` | JOIN（item_type='character'） |
| `events` | JOIN（item_type='event'） |

---

### 4.4 GET /v1/tags

**目的:** タグ一覧取得

#### Auth

| 認証 | 権限 |
|------|------|
| 必須 | オンボーディング完了 |

#### Request

```http
GET /v1/tags?type=pack
Authorization: Bearer {access_token}
```

**クエリパラメータ:**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `type` | string | — | タグ種別（`pack`, `character`） |

#### Response

**200 OK**

```json
{
  "data": [
    { "id": "tag_001", "name": "幼馴染", "count": 45 },
    { "id": "tag_002", "name": "明るい", "count": 120 },
    { "id": "tag_003", "name": "ツンデレ", "count": 89 }
  ]
}
```

#### DB 対応

| テーブル | 操作 |
|---------|------|
| `m_tags` | SELECT |
| `pack_tags` | COUNT |

---

## 5. Conversation - 会話

### 対象ストーリー

- **EU-005**: テキスト会話＋保存＋再開＋タイムアウトUX

### 対象画面

- S-030: 会話画面（新規/既存）

---

### 5.1 POST /v1/threads

**目的:** 会話スレッド作成（EU-005 / S-030 新規会話）

#### Auth

| 認証 | 権限 |
|------|------|
| 必須 | オンボーディング完了、Pack 所持 or 無料 |

#### Request

```http
POST /v1/threads
Authorization: Bearer {access_token}
Content-Type: application/json
```

```json
{
  "pack_id": "pack_001",
  "character_id": "char_001",
  "session_type": "free"
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `pack_id` | string (uuid) | ✓ | 対象 Pack ID |
| `character_id` | string (uuid) | ✓ | 対象キャラクター ID |
| `session_type` | string | — | セッション種別（`free`, `event`）デフォルト: `free` |
| `event_id` | string (uuid) | — | イベント会話の場合のイベント ID |

#### Response

**201 Created**

```json
{
  "thread": {
    "id": "thread_001",
    "pack_id": "pack_001",
    "character": {
      "id": "char_001",
      "name": "桜井 あかり",
      "avatar_url": "https://cdn.aiwill.app/characters/char_001/avatar.jpg"
    },
    "session_type": "free",
    "message_count": 0,
    "created_at": "2026-01-31T12:00:00Z",
    "updated_at": "2026-01-31T12:00:00Z"
  }
}
```

#### エラー

| HTTP | code | 条件 |
|------|------|------|
| 400 | `validation_error` | パラメータ不正 |
| 403 | `entitlement_required` | Pack 未所持 |
| 403 | `age_restricted` | 年齢制限 |
| 404 | `not_found` | Pack/キャラクターが存在しない |

#### DB 対応

| テーブル | 操作 |
|---------|------|
| `conversation_sessions` | INSERT |
| `user_entitlements` | SELECT（所持確認） |
| `characters` | SELECT |

---

### 5.2 GET /v1/threads

**目的:** スレッド一覧取得（EU-005）

#### Auth

| 認証 | 権限 |
|------|------|
| 必須 | オンボーディング完了 |

#### Request

```http
GET /v1/threads?limit=20&cursor=xxx
Authorization: Bearer {access_token}
```

**クエリパラメータ:**

| パラメータ | 型 | 必須 | 説明 | デフォルト |
|-----------|-----|------|------|-----------|
| `character_id` | string | — | キャラクター絞り込み | — |
| `sort` | string | — | ソートキー | `updated_at` |
| `order` | string | — | 昇順/降順 | `desc` |
| `cursor` | string | — | カーソル | — |
| `limit` | integer | — | 取得件数 | 20 |

#### Response

**200 OK**

```json
{
  "data": [
    {
      "id": "thread_001",
      "character": {
        "id": "char_001",
        "name": "桜井 あかり",
        "avatar_url": "https://cdn.aiwill.app/characters/char_001/avatar.jpg"
      },
      "session_type": "free",
      "message_count": 42,
      "last_message": {
        "content": "また明日ね！",
        "role": "character",
        "created_at": "2026-01-31T18:00:00Z"
      },
      "created_at": "2026-01-31T12:00:00Z",
      "updated_at": "2026-01-31T18:00:00Z"
    }
  ],
  "pagination": {
    "next_cursor": "eyJpZCI6InRocmVhZF8wMjAifQ",
    "has_more": true
  }
}
```

#### DB 対応

| テーブル | 操作 |
|---------|------|
| `conversation_sessions` | SELECT (WHERE user_id = current_user **AND deleted_at IS NULL**) |
| `characters` | JOIN |
| `conversation_messages` | LATERAL JOIN（最新メッセージ） |

**実装注意（N+1対策）:** 最新メッセージの取得は LATERAL JOIN または window 関数で一括取得すること。

---

### 5.3 GET /v1/threads/{thread_id}

**目的:** スレッド詳細取得（EU-005 / S-030）

#### Auth

| 認証 | 権限 |
|------|------|
| 必須 | オンボーディング完了、所有者 |

#### Request

```http
GET /v1/threads/thread_001
Authorization: Bearer {access_token}
```

#### Response

**200 OK**

```json
{
  "thread": {
    "id": "thread_001",
    "pack_id": "pack_001",
    "character": {
      "id": "char_001",
      "name": "桜井 あかり",
      "avatar_url": "https://cdn.aiwill.app/characters/char_001/avatar.jpg"
    },
    "session_type": "free",
    "message_count": 42,
    "created_at": "2026-01-31T12:00:00Z",
    "updated_at": "2026-01-31T18:00:00Z"
  },
  "relationship": {
    "affection": 75,
    "stage": {
      "id": "stage_003",
      "name": "仲良し",
      "code": "close_friend"
    }
  }
}
```

#### エラー

| HTTP | code | 条件 |
|------|------|------|
| 403 | `forbidden` | 他ユーザーのスレッド |
| 404 | `not_found` | スレッドが存在しない |

#### DB 対応

| テーブル | 操作 |
|---------|------|
| `conversation_sessions` | SELECT |
| `characters` | JOIN |
| `user_character_relationships` | SELECT |
| `m_relationship_stages` | JOIN |

---

### 5.4 GET /v1/threads/{thread_id}/messages

**目的:** メッセージ履歴取得（EU-005 / S-030）

#### Auth

| 認証 | 権限 |
|------|------|
| 必須 | オンボーディング完了、所有者 |

#### Request

```http
GET /v1/threads/thread_001/messages?limit=50&cursor=xxx
Authorization: Bearer {access_token}
```

**クエリパラメータ:**

| パラメータ | 型 | 必須 | 説明 | デフォルト |
|-----------|-----|------|------|-----------|
| `cursor` | string | — | カーソル | — |
| `limit` | integer | — | 取得件数（1〜100） | 50 |
| `order` | string | — | `asc`（古い順）/ `desc`（新しい順） | `desc` |

#### Response

**200 OK**

```json
{
  "data": [
    {
      "id": "msg_042",
      "role": "character",
      "content": "また明日ね！",
      "content_type": "text",
      "created_at": "2026-01-31T18:00:00Z"
    },
    {
      "id": "msg_041",
      "role": "user",
      "content": "うん、また明日！",
      "content_type": "text",
      "created_at": "2026-01-31T17:59:30Z"
    }
  ],
  "pagination": {
    "next_cursor": "eyJpZCI6Im1zZ18wMjAifQ",
    "has_more": true
  }
}
```

#### DB 対応

| テーブル | 操作 |
|---------|------|
| `conversation_messages` | SELECT |

---

### 5.5 POST /v1/threads/{thread_id}/messages

**目的:** メッセージ送信（EU-005 / S-030）

#### Auth

| 認証 | 権限 |
|------|------|
| 必須 | オンボーディング完了、所有者 |

#### Request

```http
POST /v1/threads/thread_001/messages
Authorization: Bearer {access_token}
Content-Type: application/json
```

```json
{
  "content": "こんにちは！今日はいい天気だね",
  "content_type": "text"
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `content` | string | ✓ | メッセージ内容 |
| `content_type` | string | — | `text` / `audio`（デフォルト: `text`） |

#### Response

**201 Created**

> メッセージ送信はリソース作成のため `201` を返却します。

```json
{
  "user_message": {
    "id": "msg_043",
    "role": "user",
    "content": "こんにちは！今日はいい天気だね",
    "content_type": "text",
    "created_at": "2026-01-31T19:00:00Z"
  },
  "assistant_message": {
    "id": "msg_044",
    "role": "character",
    "content": "うん！こんな日はお散歩に行きたくなるね。一緒に行く？",
    "content_type": "text",
    "created_at": "2026-01-31T19:00:02Z"
  }
}
```

#### エラー

| HTTP | code | 条件 |
|------|------|------|
| 400 | `validation_error` | 空メッセージ等 |
| 403 | `forbidden` | 他ユーザーのスレッド |
| 408 | `request_timeout` | LLM 応答タイムアウト |
| 503 | `service_unavailable` | LLM サービス障害 |

#### DB 対応

| テーブル | 操作 |
|---------|------|
| `conversation_messages` | INSERT × 2（user + character） |
| `conversation_sessions` | UPDATE（updated_at, message_count） |
| `user_character_relationships` | UPDATE（affection） |
| `user_character_memories` | UPDATE（必要に応じて） |

---

### 5.6 POST /v1/threads/{thread_id}/messages:stream

**目的:** メッセージ送信（SSE ストリーミング）（EU-005）

#### Auth

| 認証 | 権限 |
|------|------|
| 必須 | オンボーディング完了、所有者 |

#### Request

```http
POST /v1/threads/thread_001/messages:stream
Authorization: Bearer {access_token}
Content-Type: application/json
Accept: text/event-stream
```

```json
{
  "content": "こんにちは！",
  "content_type": "text"
}
```

#### Response

**200 OK (text/event-stream)**

```
event: message_start
data: {"user_message_id": "msg_043", "assistant_message_id": "msg_044"}

event: content_delta
data: {"delta": "うん！"}

event: content_delta
data: {"delta": "こんな日は"}

event: content_delta
data: {"delta": "お散歩に行きたくなるね。"}

event: content_delta
data: {"delta": "一緒に行く？"}

event: message_end
data: {"assistant_message_id": "msg_044", "finish_reason": "stop"}
```

**SSE イベント:**

| イベント | データ | 説明 |
|----------|--------|------|
| `message_start` | `user_message_id`, `assistant_message_id` | 開始 |
| `content_delta` | `delta` | テキスト差分 |
| `message_end` | `finish_reason` | 完了 |
| `error` | `code`, `message` | エラー |

#### エラー（SSE 内）

```
event: error
data: {"code": "request_timeout", "message": "応答がタイムアウトしました。再度お試しください。"}
```

#### DB 対応

5.5 と同様

---

## 6. Safety - 通報

### 対象ストーリー

- **EU-007**: 通報（基本）

### 対象画面

- M-001: 通報モーダル（S-021, S-030 から起動）

---

### 6.1 GET /v1/report-reasons

**目的:** 通報理由一覧取得

#### Auth

| 認証 | 権限 |
|------|------|
| 必須 | オンボーディング完了 |

#### Request

```http
GET /v1/report-reasons
Authorization: Bearer {access_token}
```

#### Response

**200 OK**

```json
{
  "data": [
    { "id": "reason_001", "code": "inappropriate_content", "name": "不適切なコンテンツ" },
    { "id": "reason_002", "code": "harassment", "name": "ハラスメント" },
    { "id": "reason_003", "code": "spam", "name": "スパム" },
    { "id": "reason_004", "code": "copyright", "name": "著作権侵害" },
    { "id": "reason_005", "code": "other", "name": "その他" }
  ]
}
```

#### DB 対応

| テーブル | 操作 |
|---------|------|
| `m_report_reasons` | SELECT |

---

### 6.2 POST /v1/reports

**目的:** 通報送信（EU-007 / M-001）

#### Auth

| 認証 | 権限 |
|------|------|
| 必須 | オンボーディング完了 |

#### Request

```http
POST /v1/reports
Authorization: Bearer {access_token}
Content-Type: application/json
```

```json
{
  "target_type": "character",
  "target_id": "char_001",
  "reason_id": "reason_001",
  "comment": "不適切な発言がありました"
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `target_type` | string | ✓ | 通報対象種別（`character`, `message`, `pack`, `creator`） |
| `target_id` | string (uuid) | ✓ | 通報対象 ID |
| `reason_id` | string (uuid) | ✓ | 通報理由 ID |
| `comment` | string | — | 補足コメント（最大500文字） |

#### Response

**201 Created**

```json
{
  "report": {
    "id": "report_001",
    "target_type": "character",
    "target_id": "char_001",
    "reason": {
      "id": "reason_001",
      "name": "不適切なコンテンツ"
    },
    "status": "open",
    "created_at": "2026-01-31T12:00:00Z"
  },
  "message": "通報を受け付けました。ご協力ありがとうございます。"
}
```

#### エラー

| HTTP | code | 条件 |
|------|------|------|
| 400 | `validation_error` | パラメータ不正 |
| 404 | `not_found` | 通報対象が存在しない |
| 409 | `duplicate_report` | 同一対象への重複通報（24時間以内） |

#### DB 対応

| テーブル | 操作 |
|---------|------|
| `reports` | INSERT |
| `m_report_reasons` | SELECT（検証） |
| 対象テーブル | SELECT（存在確認） |

---

## 7. Privacy - 会話履歴削除

### 対象ストーリー

- **EU-008**: 会話履歴削除

### 対象画面

- S-040: 設定
- M-003: 削除確認モーダル

---

### 7.1 DELETE /v1/threads/{thread_id}

**目的:** 会話スレッド削除（EU-008）

#### Auth

| 認証 | 権限 |
|------|------|
| 必須 | オンボーディング完了、所有者 |

#### Request

```http
DELETE /v1/threads/thread_001
Authorization: Bearer {access_token}
```

#### Response

**204 No Content**

#### エラー

| HTTP | code | 条件 |
|------|------|------|
| 403 | `forbidden` | 他ユーザーのスレッド |
| 404 | `not_found` | スレッドが存在しない |

#### DB 対応

| テーブル | 操作 |
|---------|------|
| `conversation_sessions` | UPDATE（deleted_at） |
| `conversation_messages` | UPDATE（deleted_at）※論理削除 |

---

### 7.2 ~~DELETE /v1/threads~~ (MVP から削除)

> **NOTE:** 一括削除 API は MVP から削除しました。
> - **理由:** Privacy Job（`POST /v1/privacy/delete`）で会話履歴の一括削除に対応可能
> - **個別削除:** `DELETE /v1/threads/{thread_id}` で対応

---

### 7.3 POST /v1/privacy/delete

**目的:** データ削除ジョブ作成（EU-008 全データ削除）

#### Auth

| 認証 | 権限 |
|------|------|
| 必須 | オンボーディング完了 |

#### Request

```http
POST /v1/privacy/delete
Authorization: Bearer {access_token}
Idempotency-Key: {uuid}
Content-Type: application/json
```

```json
{
  "scope": "all",
  "confirm": true
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `scope` | string | ✓ | 削除範囲（`conversations`, `memories`, `all`） |
| `confirm` | boolean | ✓ | 確認フラグ（`true` 必須） |

#### Response

**202 Accepted**

```json
{
  "job_id": "job_delete_001",
  "status": "queued",
  "scope": "all",
  "created_at": "2026-01-31T12:00:00Z",
  "estimated_completion": "2026-01-31T12:05:00Z",
  "grace_period_until": "2026-02-07T12:00:00Z"
}
```

**grace_period_until:** 猶予期間（この日時までキャンセル可能）

#### エラー

| HTTP | code | 条件 |
|------|------|------|
| 400 | `confirmation_required` | `confirm=true` 未指定 |
| 400 | `idempotency_key_required` | Idempotency-Key 未指定 |
| 409 | `job_in_progress` | 既存のジョブが進行中 |

#### DB 対応

| テーブル | 操作 |
|---------|------|
| `data_deletion_requests` | INSERT |
| `audit_logs` | INSERT |

---

### 7.4 GET /v1/privacy/delete/{job_id}

**目的:** 削除ジョブ状態確認

#### Auth

| 認証 | 権限 |
|------|------|
| 必須 | 所有者 |

#### Request

```http
GET /v1/privacy/delete/job_delete_001
Authorization: Bearer {access_token}
```

#### Response

**200 OK**

```json
{
  "job_id": "job_delete_001",
  "status": "processing",
  "scope": "all",
  "progress": {
    "total_items": 1000,
    "processed_items": 350,
    "percentage": 35
  },
  "created_at": "2026-01-31T12:00:00Z",
  "updated_at": "2026-01-31T12:02:00Z",
  "grace_period_until": "2026-02-07T12:00:00Z"
}
```

**status:**

| status | 説明 |
|--------|------|
| `queued` | 待機中 |
| `processing` | 処理中 |
| `completed` | 完了 |
| `cancelled` | キャンセル済み |
| `failed` | 失敗 |

#### DB 対応

| テーブル | 操作 |
|---------|------|
| `data_deletion_requests` | SELECT |

---

### 7.5 POST /v1/privacy/delete/{job_id}/cancel

**目的:** 削除ジョブキャンセル

#### Auth

| 認証 | 権限 |
|------|------|
| 必須 | 所有者 |

#### Request

```http
POST /v1/privacy/delete/job_delete_001/cancel
Authorization: Bearer {access_token}
```

#### Response

**200 OK**

```json
{
  "job_id": "job_delete_001",
  "status": "cancelled",
  "cancelled_at": "2026-01-31T12:03:00Z"
}
```

#### エラー

| HTTP | code | 条件 |
|------|------|------|
| 400 | `cannot_cancel` | 猶予期間終了または処理完了後 |

#### DB 対応

| テーブル | 操作 |
|---------|------|
| `data_deletion_requests` | UPDATE（status） |

---

## 8. Open Questions

### 8.0 DB スキーマ修正が必要な項目（P0/P1）

以下の項目は API 設計確定済みだが、DB スキーマ修正が必要:

| 項目 | API | DB | 推奨対応 | 優先度 |
|------|-----|----|---------|----|
| **content_type カラム** | `Message.content_type: text/audio` | `conversation_messages` に該当カラムなし | `content_type VARCHAR(20) NOT NULL DEFAULT 'text'` を追加 | **P0** |
| **memory_clips の title/tags** | `Clip.title`, `Clip.tags` | `memory_clips` に該当カラムなし | `title VARCHAR(100)`, `tags TEXT[]` を追加 | **P1** |

**注**: これらは DB 設計書（database_design.md）の修正として別途対応すること。

### 8.1 認証・セキュリティ

| 項目 | 疑問点 | 暫定決定 |
|------|--------|----------|
| トークン保存 | アクセストークンの保存場所（Cookie vs LocalStorage） | LocalStorage（XSS 対策は別途） |
| セッション管理 | 同時ログイン数制限 | 制限なし（MVP） |
| パスワード要件 | 詳細なパスワードポリシー | 8文字以上、英数必須（MVP） |

### 8.2 年齢確認

| 項目 | 疑問点 | 暫定決定 |
|------|--------|----------|
| 年齢変更 | 年齢情報の変更フロー | 不可（サポート対応） |
| 検証方法 | 生年月日の真正性確認 | 自己申告（MVP） |
| u13 対応 | 13歳未満の利用可否 | 利用不可（登録時にブロック） |

### 8.3 会話

| 項目 | 疑問点 | 暫定決定 |
|------|--------|----------|
| タイムアウト | LLM 応答のタイムアウト値 | 30秒 |
| リトライ | クライアントでのリトライ戦略 | 手動リトライボタン表示 |
| メッセージ長 | 1メッセージの最大文字数 | 2000文字 |
| 履歴保持 | スレッド内のメッセージ上限 | 上限なし（MVP） |

### 8.4 通報

| 項目 | 疑問点 | 暫定決定 |
|------|--------|----------|
| 重複抑制 | 同一対象への重複通報の期間 | 24時間 |
| 匿名性 | 通報者情報の開示 | 非開示（運営のみ参照可） |
| 通知 | 通報受付の通知方法 | API レスポンスのみ（メール通知なし） |

### 8.5 削除

| 項目 | 疑問点 | 暫定決定 |
|------|--------|----------|
| 猶予期間 | 全データ削除の猶予期間 | 7日間 |
| 物理削除 | 猶予期間後の物理削除タイミング | 猶予期間終了後バッチで実行 |
| 監査ログ | 削除後の監査ログ保持 | 削除しない（永続保持） |

### 8.6 Phase 2 以降への持ち越し

| 項目 | 理由 |
|------|------|
| 購入 API | Phase 2 で実装 |
| ブロック API | Phase 2 で実装 |
| メモリー（切り抜き）API | Phase 2 で実装 |
| エクスポート API | Phase 3 で実装 |
| 音声モード | Phase 3 で実装 |
| ソーシャルログイン | Phase 3 で実装 |

---

## 改訂履歴

| バージョン | 日付 | 変更内容 |
|------------|------|----------|
| 1.0.0 | 2026-01-31 | 初版作成（MVP Phase 1 対応） |
| 1.1.0 | 2026-01-31 | review.md P0/P1 反映: Pack一覧の年齢フィルタ追加、論理削除条件明記、N+1対策明記、DBスキーマ修正事項をOpen Questionsに追加 |

---

## 参照ドキュメント

- [rules/api.mdc](../../rules/api.mdc) - API 設計規約
- [requirements.md](../../requirements.md) - 要件定義書
- [screens.md](../../screens.md) - 画面設計書
- [user_stories_end_user.md](../../user_stories_end_user.md) - ユーザーストーリー
- [prioritization_end_user.md](../../prioritization_end_user.md) - 優先順位
- [entities.md](../../entities.md) - エンティティ一覧
- [database_design.md](../../database_design.md) - テーブル設計書
