# AI will API 整合性レビュー

| 項目 | 内容 |
|------|------|
| ドキュメント名 | API整合性レビュー |
| バージョン | 1.2.0 |
| 作成日 | 2026-01-31 |
| 最終更新日 | 2026-01-31 |
| 対象 | api.md, openapi.yaml, app/ (FastAPI) |
| 突き合わせ | database_design.md, entities.md, screens.md, user_stories_end_user.md |

---

## 指摘事項の優先度分類

### P0: 今すぐ修正しないと実装が詰む

| # | 指摘 | セクション | 対応状況 |
|---|------|-----------|---------|
| P0-1 | Pack一覧の年齢制限フィルタ漏れ | 3.1 | ✅ **反映済み** - api.md/openapi.yaml に年齢自動フィルタを追加 |
| P0-2 | 論理削除（deleted_at）の考慮漏れ | 6.4 | ✅ **反映済み** - api.md の DB操作に `deleted_at IS NULL` を明記 |
| P0-3 | conversation_messages に content_type がない | 7.2 | 📝 **Open Questions** - DB修正が必要。API設計は維持 |
| P0-4 | DELETE /v1/threads 一括削除の設計曖昧 | 2.2 | ✅ **反映済み** (v1.2.0) - MVP不要と判断し削除。Privacy Job で代替可能 |
| P0-5 | POST /messages ステータス 200 → 201 | 5.5 | ✅ **反映済み** (v1.2.0) - メッセージ作成は 201 に修正 |
| P0-6 | 削除系ステータスの不統一 | — | ✅ **反映済み** (v1.2.0) - 原則 204（bodyなし）に統一 |

### P1: 実装開始後に手戻りになる

| # | 指摘 | セクション | 対応状況 |
|---|------|-----------|---------|
| P1-1 | memory_clips に title/tags がない | 7.2 | 📝 **Open Questions** - DB修正が必要。API設計は維持 |
| P1-2 | PATCH /v1/clips の設計判断 | 7.2 | ✅ **反映済み** - 推奨案A採用：編集不可としてAPIから削除 |
| P1-3 | N+1問題のリスク | 6.1 | ✅ **反映済み** - api.md に実装注意事項として明記 |

### P2: 品質改善（Phase 2以降で対応）

| # | 指摘 | セクション | 対応状況 |
|---|------|-----------|---------|
| P2-1 | お気に入りAPI不足 | 1.1 | Phase 2 で対応 |
| P2-2 | ブロックフィルタ | 3.3 | Phase 2 で対応 |
| P2-3 | スレッド作成の冪等性 | 4.3 | 任意対応（検討中） |

---

## 目次

1. [不足しているエンドポイント](#1-不足しているエンドポイント)
2. [余計なエンドポイント](#2-余計なエンドポイント)
3. [権限漏れ](#3-権限漏れ)
4. [冪等性の漏れ](#4-冪等性の漏れ)
5. [非同期ジョブ設計の問題](#5-非同期ジョブ設計の問題)
6. [DB参照/更新の問題](#6-db参照更新の問題)
7. [API/DB間の不整合](#7-apidb間の不整合)
8. [修正提案](#8-修正提案)

---

## 1. 不足しているエンドポイント

### 1.1 Phase 1（MVP）で不足

| 不足API | 関連画面/ストーリー | DBテーブル | 重要度 | 備考 |
|---------|-------------------|------------|--------|------|
| `POST /v1/favorites` | S-021 詳細画面（お気に入り） | `user_favorites` | **Should** | EU-003「所持済み/未所持/無料などのステータスが分かる表示」に関連。Phase 2 Shouldだが、DBテーブルは存在 |
| `DELETE /v1/favorites/{id}` | S-021 詳細画面 | `user_favorites` | **Should** | 同上 |
| `GET /v1/favorites` | マイライブラリ（画面定義なし） | `user_favorites` | **Could** | 画面定義なし。MVP後検討 |

### 1.2 Phase 2 で必要（api.md に未記載）

以下は `openapi.yaml` には含まれているが、`api.md` の MVP 範囲には記載なし（正しい）:

| API | Phase | 備考 |
|-----|-------|------|
| 購入系（purchases, entitlements） | Phase 2 | ✓ openapi.yaml に定義済み |
| ブロック系（blocks） | Phase 2 | ✓ openapi.yaml に定義済み |
| メモリー系（clips） | Phase 2 | ✓ openapi.yaml に定義済み |
| エクスポート（privacy/export） | Phase 3 | ✓ openapi.yaml に定義済み |

### 1.3 完全に不足しているAPI

| 不足API | 関連機能 | DBテーブル | 重要度 |
|---------|---------|------------|--------|
| `GET /v1/relationship-stages` | 関係ステージマスタ | `m_relationship_stages` | Low |
| `GET /v1/characters/{id}` | キャラクター単体取得 | `characters` | Low（Pack経由で取得可能） |

---

## 2. 余計なエンドポイント

### 2.1 画面に紐づかないが必要なAPI

| API | 理由 | 判定 |
|-----|------|------|
| `GET /v1/tags` | 検索/フィルタ用。Phase 2 の高度検索で必要 | **残す** |
| `GET /v1/packs/{pack_id}/items` | Pack 詳細画面で構成アイテム表示 | **残す** |
| `GET /v1/report-reasons` | 通報モーダルで理由選択肢を動的取得 | **残す** |

### 2.2 削除検討API

| API | 理由 | 判定 |
|-----|------|------|
| なし | — | — |

**結論**: 余計なエンドポイントは見当たらない。

---

## 3. 権限漏れ

### 3.1 年齢制限チェックの漏れ

| API | 現状 | 問題 | 対応 |
|-----|------|------|------|
| `GET /v1/packs` | 年齢制限なし | 成人向け Pack が未成年ユーザーの一覧に表示される可能性 | フィルタ条件に `age_rating` を追加し、`user.age_group` に応じてフィルタ |
| `GET /v1/packs/{pack_id}` | 403 `age_restricted` を返す | ✓ 対応済み | — |
| `POST /v1/threads` | 403 `age_restricted` を返す | ✓ 対応済み | — |

### 3.2 購入チェックの漏れ

| API | 現状 | 問題 | 対応 |
|-----|------|------|------|
| `POST /v1/threads` | 403 `entitlement_required` | ✓ 対応済み | — |
| `GET /v1/threads/{thread_id}/messages` | 所有者チェックのみ | 問題なし（スレッドが作成できている＝購入済み or 無料） | — |

### 3.3 ブロックチェックの漏れ

| API | 現状 | 問題 | 対応 |
|-----|------|------|------|
| `GET /v1/packs` | ブロックフィルタなし | ブロック済みの Creator/Character の Pack が表示される | **Phase 2 で対応**: クエリに `user_blocks` を考慮 |
| `POST /v1/threads` | ブロックチェックなし | ブロック済みキャラクターとの会話開始が可能 | **Phase 2 で対応**: 403 `blocked` を追加 |

### 3.4 オンボーディング完了チェックの漏れ

| API | 現状 | 問題 | 対応 |
|-----|------|------|------|
| すべてのメイン機能API | `requireCompleted` 相当 | ✓ api.md に記載済み | — |

---

## 4. 冪等性の漏れ

### 4.1 現状の Idempotency-Key 必須API

| API | Idempotency-Key | 判定 |
|-----|-----------------|------|
| `POST /v1/purchases` | ✓ 必須 | OK |
| `POST /v1/purchases:restore` | ✓ 必須 | OK |
| `POST /v1/privacy/export` | ✓ 必須 | OK |
| `POST /v1/privacy/delete` | ✓ 必須 | OK |

### 4.2 冪等性が必要な可能性があるAPI

| API | 現状 | リスク | 判定 |
|-----|------|--------|------|
| `POST /v1/reports` | なし | 同一対象への重複通報（24時間制限あり） | **不要**: 重複通報は 409 `duplicate_report` で対応済み |
| `POST /v1/threads` | なし | 同一リクエストで複数スレッド作成 | **検討**: ネットワーク再送で重複作成の可能性あり |
| `POST /v1/clips` | なし | 同一メッセージから重複クリップ作成 | **不要**: 複数クリップ許可の設計意図 |
| `POST /v1/blocks` | なし | 同一対象への重複ブロック | **不要**: 409 `conflict` で対応可能 |

### 4.3 推奨追加

| API | 推奨 | 理由 |
|-----|------|------|
| `POST /v1/threads` | **Idempotency-Key 推奨** | モバイルアプリでのネットワーク不安定時、再送で重複スレッドが作成される可能性。ただし、UXとしては複数スレッドを許容する設計のため **任意** |

---

## 5. 非同期ジョブ設計の問題

### 5.1 現状の非同期ジョブAPI

| API | ジョブ形式 | 判定 |
|-----|-----------|------|
| `POST /v1/privacy/export` | ✓ 202 Accepted + job_id | OK |
| `POST /v1/privacy/delete` | ✓ 202 Accepted + job_id | OK |

### 5.2 同期で設計されているが問題ないAPI

| API | 理由 | 判定 |
|-----|------|------|
| `POST /v1/threads/{id}/messages` | SSEストリーミング版（`:stream`）で非同期対応済み | OK |
| `POST /v1/purchases` | 外部決済APIは同期的にレシート検証。タイムアウト30秒以内で完了想定 | OK |

### 5.3 非同期ジョブにすべき可能性があるAPI

| API | 現状 | リスク | 推奨 |
|-----|------|--------|------|
| 画像生成（未定義） | — | — | Phase 3 で定義時に非同期ジョブ形式で設計（`openapi.yaml` に定義済み） |
| TTS（未定義） | — | — | Phase 3 で定義時、SSEストリーミングまたは非同期ジョブで設計 |

---

## 6. DB参照/更新の問題

### 6.1 N+1問題のリスク

| API | 問題箇所 | 影響 | 対応策 |
|-----|---------|------|--------|
| `GET /v1/packs` | `tags` 配列の取得 | Pack ごとに `pack_tags` + `m_tags` をクエリすると N+1 | **対応**: JOINまたはサブクエリで一括取得。レスポンスのタグは最大10件に制限 |
| `GET /v1/threads` | `last_message` の取得 | スレッドごとに最新メッセージを取得すると N+1 | **対応**: LATERAL JOIN または window 関数で一括取得 |
| `GET /v1/clips` | `character` の取得 | クリップごとにキャラクター情報を取得すると N+1 | **対応**: JOINで一括取得 |

### 6.2 巨大レスポンスのリスク

| API | 問題箇所 | 影響 | 対応策 |
|-----|---------|------|--------|
| `GET /v1/threads/{id}/messages` | メッセージ履歴 | 長期間の会話で数万件になる可能性 | ✓ **対応済み**: ページング（limit 最大100） |
| `GET /v1/packs` | Pack 一覧 | 数千件になる可能性 | ✓ **対応済み**: ページング（limit 最大100） |

### 6.3 結合前提の問題

| API | DB操作 | 問題 | 対応策 |
|-----|--------|------|--------|
| `GET /v1/packs/{pack_id}` | `user_entitlements`, `user_favorites` を別クエリ | 2回の追加クエリ | **最適化**: 1クエリで LEFT JOIN 可能だが、キャッシュ戦略（ユーザー別の所持状況）によっては分離が適切 |
| `GET /v1/threads/{thread_id}` | `user_character_relationships` を別クエリ | 1回の追加クエリ | **許容**: 関係情報は会話体験に重要。キャッシュ推奨 |

### 6.4 論理削除の考慮漏れ

| API | 問題 | 対応 |
|-----|------|------|
| `GET /v1/threads` | 削除済みスレッド（`deleted_at IS NOT NULL`）の除外が明示されていない | **修正**: クエリ条件に `WHERE deleted_at IS NULL` を追加（api.md に明記） |
| `GET /v1/clips` | 同上 | **修正**: 同上 |
| `GET /v1/blocks` | 同上 | **修正**: 同上（`openapi.yaml` では `active` ブロックのみ取得と想定） |

---

## 7. API/DB間の不整合

### 7.1 テーブル名/リソース名のマッピング

| API リソース | DB テーブル | 備考 |
|-------------|------------|------|
| `Thread` | `conversation_sessions` | セッション＝スレッドの概念 |
| `Message` | `conversation_messages` | — |
| `Clip` | `memory_clips` | — |
| `Pack` | `packs` | — |
| `User` | `users` | — |
| `Entitlement` | `user_entitlements` | — |
| `Purchase` | `purchases` | — |
| `Report` | `reports` | — |
| `Block` | `user_blocks` | — |

### 7.2 カラムの不整合

| 問題 | API | DB | 対応 |
|------|-----|----|----|
| **content_type カラムが存在しない** | `Message.content_type: text/audio` | `conversation_messages` に `content_type` カラムなし | **DB修正が必要**: `content_type VARCHAR(20) DEFAULT 'text'` を追加 |
| **memory_clips に title/tags がない** | `Clip.title`, `Clip.tags` | `memory_clips` に該当カラムなし | **DB修正が必要**: `title VARCHAR(100)`, `tags TEXT[]` を追加 |
| **memory_clips は更新不可** | `PATCH /v1/clips/{id}` で更新可能 | `memory_clips` は `updated_at` を持たない（作成のみ） | **設計判断**: (A) APIから PATCH を削除、または (B) DB に `updated_at` を追加 |

### 7.3 DBに存在するがAPIで未使用のテーブル

| テーブル | 用途 | MVP対応 |
|---------|------|---------|
| `user_creator_follows` | クリエイターフォロー | Phase 2 以降 |
| `user_character_relationships` | 好感度・関係ステージ | 会話詳細で返却（`GET /v1/threads/{id}`） |
| `user_character_flags` | 告白済み等のフラグ | Phase 2 以降（イベント解放条件） |
| `user_character_memories` | 長期記憶（呼び方、好み等） | 内部利用（LLMプロンプト用）。APIで公開しない |
| `voice_packs`, `voice_assets` | ボイスパック | Phase 3（音声モード） |
| `events`, `event_*` | イベント系 | Phase 2 以降（イベント会話） |
| `ticket_*` | チケット/クレジット | Phase 2 以降（課金モデル次第） |
| `creator_*`, `payout_*` | クリエイター収益 | クリエイター向けAPI（別途設計） |
| `admin_users`, `moderation_actions`, `appeals` | 運営機能 | 運営コンソールAPI（別途設計） |
| `notifications` | 通知 | Phase 2 以降 |

---

## 8. 修正提案

### 8.1 api.md への修正

#### 8.1.1 Pack 一覧の年齢制限フィルタ追加

```diff
 ### 4.1 GET /v1/packs
 
 **クエリパラメータ:**
 
 | パラメータ | 型 | 必須 | 説明 | デフォルト |
 |-----------|-----|------|------|-----------|
 | `type` | string | — | Pack 種別（`persona`, `scenario`） | 全種別 |
 | `query` | string | — | キーワード検索（名前、説明） | — |
 | `tags` | string | — | タグ絞り込み（カンマ区切り） | — |
+| `age_rating` | string | — | 年齢レーティング（`all`, `r15`, `r18`） | — |
 | `sort` | string | — | ソートキー | `created_at` |
 
+**注意**: ユーザーの `age_group` に応じて、閲覧可能な `age_rating` が自動的にフィルタされる。
+- `u13`: `all` のみ
+- `u18`: `all`, `r15`
+- `adult`: すべて
```

#### 8.1.2 論理削除の明示

```diff
 ### 5.2 GET /v1/threads
 
 #### DB 対応
 
 | テーブル | 操作 |
 |---------|------|
-| `conversation_sessions` | SELECT (WHERE user_id = current_user) |
+| `conversation_sessions` | SELECT (WHERE user_id = current_user AND deleted_at IS NULL) |
 | `characters` | JOIN |
 | `conversation_messages` | LATERAL JOIN（最新メッセージ） |
```

#### 8.1.3 Phase 2 用お気に入りAPI追加（参考）

```markdown
### 4.5 POST /v1/favorites（Phase 2）

**目的:** お気に入り登録

#### Request
POST /v1/favorites
{
  "character_id": "char_001"
}

#### Response
201 Created
{
  "favorite": {
    "id": "fav_001",
    "character_id": "char_001",
    "created_at": "2026-01-31T12:00:00Z"
  }
}

### 4.6 DELETE /v1/favorites/{favorite_id}（Phase 2）

**目的:** お気に入り解除

#### Response
204 No Content
```

### 8.2 openapi.yaml への修正

#### 8.2.1 Pack 一覧に年齢フィルタ追加

```yaml
/packs:
  get:
    parameters:
      # ... 既存パラメータ ...
      - name: age_rating
        in: query
        schema:
          type: string
          enum: [all, r15, r18]
        description: 年齢レーティングフィルタ
```

#### 8.2.2 お気に入りAPIスキーマ追加（Phase 2）

```yaml
# schemas に追加
Favorite:
  type: object
  properties:
    id:
      type: string
      format: uuid
    character_id:
      type: string
      format: uuid
    created_at:
      type: string
      format: date-time

# paths に追加
/favorites:
  post:
    tags: [Catalog]
    summary: お気に入り登録
    # ...
  get:
    tags: [Catalog]
    summary: お気に入り一覧
    # ...

/favorites/{favorite_id}:
  delete:
    tags: [Catalog]
    summary: お気に入り解除
    # ...
```

### 8.3 database_design.md への修正提案

#### 8.3.1 conversation_messages に content_type 追加

```sql
ALTER TABLE conversation_messages
ADD COLUMN content_type VARCHAR(20) NOT NULL DEFAULT 'text'
CHECK (content_type IN ('text', 'audio'));
```

#### 8.3.2 memory_clips に title/tags 追加（設計判断次第）

**Option A: 編集不可のまま維持（推奨）**
- APIから `PATCH /v1/clips/{id}` を削除
- `memory_clips` は作成時のみタイトル/タグを設定
- DB変更: `title VARCHAR(100)`, `tags TEXT[]` を追加するが `updated_at` は追加しない

**Option B: 編集可能にする**
- `memory_clips` に `updated_at` を追加
- entities.md の「updated_at を持たないテーブル」リストから削除

```sql
-- Option A（推奨）
ALTER TABLE memory_clips
ADD COLUMN title VARCHAR(100),
ADD COLUMN tags TEXT[];

-- Option B
ALTER TABLE memory_clips
ADD COLUMN title VARCHAR(100),
ADD COLUMN tags TEXT[],
ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
```

---

## 9. 優先度別対応サマリー

### 9.1 緊急（MVP リリース前に対応必須）

| 項目 | 対応内容 |
|------|---------|
| DB: `conversation_messages.content_type` | カラム追加 |
| API: 論理削除考慮 | `deleted_at IS NULL` 条件の明示 |
| API: Pack 一覧の年齢フィルタ | クエリ条件追加 |

### 9.2 重要（Phase 2 開始前に対応）

| 項目 | 対応内容 |
|------|---------|
| DB: `memory_clips` 設計見直し | title/tags カラム追加、編集可否の判断 |
| API: お気に入り機能 | エンドポイント追加 |
| API: ブロックフィルタ | Pack 一覧/会話作成でのブロック考慮 |

### 9.3 推奨（品質向上）

| 項目 | 対応内容 |
|------|---------|
| N+1 対策 | JOIN/サブクエリの最適化ガイドライン追記 |
| スレッド作成の冪等性 | Idempotency-Key 任意対応 |

---

## 10. 設計方針の統一（v1.2.0 追記）

### 10.1 HTTPステータスコードの統一

| 操作 | ステータス | body | 備考 |
|------|-----------|------|------|
| リソース作成 | **201 Created** | あり | POST でリソース生成する場合 |
| リソース削除 | **204 No Content** | なし | 個別削除、全削除問わず |
| 既存リソース取得 | 200 OK | あり | — |
| 既存リソース更新 | 200 OK | あり | PATCH/PUT |
| 非同期ジョブ開始 | **202 Accepted** | あり（job_id） | Privacy Job 等 |

### 10.2 一括操作の設計方針

| 操作 | 方針 | 理由 |
|------|------|------|
| 一括削除（会話） | `POST /privacy/delete` で代替 | 非同期ジョブで安全に処理。猶予期間・キャンセル可能 |
| 一括削除（即時） | MVP では不採用 | 意図しない大量削除を防ぐ。将来必要なら `:bulk-delete` 形式で明示 |

### 10.3 削除 API の設計ガイドライン

```
# 推奨パターン
DELETE /v1/threads/{thread_id}    → 204 No Content（個別削除）
POST /v1/privacy/delete           → 202 Accepted + job_id（一括削除）

# 非推奨パターン（MVP不採用）
DELETE /v1/threads?confirm=true   → 曖昧な一括削除
DELETE /v1/threads:bulk-delete    → 明示的だが Privacy Job で代替可能
```

---

## 改訂履歴

| バージョン | 日付 | 変更内容 |
|------------|------|----------|
| 1.0.0 | 2026-01-31 | 初版作成 |
| 1.1.0 | 2026-01-31 | P0/P1/P2 分類追加、P0/P1 反映済みステータス更新 |
| 1.2.0 | 2026-01-31 | P0-4〜P0-6 追加・反映（DELETE /threads 削除、POST /messages 201化、削除系 204 統一）|
