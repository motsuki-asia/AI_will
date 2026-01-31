# AI will テーブル設計書

| 項目           | 内容                                                     |
| -------------- | -------------------------------------------------------- |
| ドキュメント名 | AI will テーブル設計書                                   |
| バージョン     | 1.0.2                                                    |
| 作成日         | 2026-01-31                                               |
| DB             | PostgreSQL                                               |
| 参照元         | er_diagram.md, entities.md, relationships.md, screens.md |

---

## 1. 共通方針

### 1.1 DB 前提

| 項目     | 内容                                                                                 |
| -------- | ------------------------------------------------------------------------------------ |
| RDBMS    | PostgreSQL                                                                           |
| 拡張機能 | `CREATE EXTENSION IF NOT EXISTS pgcrypto;`（UUID 生成に `gen_random_uuid()` を使用） |

### 1.2 論理削除方針

| 項目            | 方針                                                                                                                |
| --------------- | ------------------------------------------------------------------------------------------------------------------- |
| 原則            | 物理削除は行わず、`deleted_at` による**論理削除**＋必要に応じて**PII 匿名化**で対応                                 |
| UNIQUE 制約     | 論理削除で再登録を許容する場合、**部分 UNIQUE INDEX（WHERE deleted_at IS NULL）** で担保                            |
| join 系テーブル | 中間テーブル（character_tags, pack_tags, pack_items, user_creator_follows, user_favorites）にも `deleted_at` を追加 |

**論理削除の例外テーブル**:

| テーブル              | 削除方針                     | 理由                     |
| --------------------- | ---------------------------- | ------------------------ |
| conversation_messages | 削除しない（永続保存）       | 会話ログは証跡として保持 |
| audit_logs            | 削除しない（イミュータブル） | 監査ログは改ざん防止     |
| purchases             | 削除しない                   | 会計証跡                 |
| ticket_transactions   | 削除しない                   | 会計証跡                 |

**監査カラムの例外（updated_at を持たないテーブル）**:

| テーブル               | 理由                                       |
| ---------------------- | ------------------------------------------ |
| ticket_transactions    | イミュータブルなログ（作成後に更新しない） |
| user_character_flags   | フラグの付与/削除のみ（更新なし）          |
| memory_clips           | 作成のみ（編集なし）                       |
| user_event_completions | クリア記録のみ（更新なし）                 |
| rights_consents        | 同意記録のみ（更新なし）                   |
| terms_agreements       | 同意記録のみ（更新なし）                   |
| payout_line_items      | 明細記録のみ（更新なし）                   |
| conversation_messages  | メッセージログ（更新なし）                 |
| audit_logs             | 監査ログ（イミュータブル）                 |

### 1.3 監査カラム（全テーブル共通）

| カラム     | type        | null | default           | 説明                                                            |
| ---------- | ----------- | ---- | ----------------- | --------------------------------------------------------------- |
| id         | uuid        | NO   | gen_random_uuid() | 主キー                                                          |
| created_at | timestamptz | NO   | now()             | 作成日時（ユーザー入力禁止）                                    |
| updated_at | timestamptz | NO   | now()             | 更新日時（UPDATE 時にアプリ/トリガーでセット）※例外テーブルあり |
| deleted_at | timestamptz | YES  | —                 | 論理削除日時（該当テーブルのみ）                                |

### 1.4 URL 共通ルール（セキュリティ）

| ルール        | 内容                                                                                     |
| ------------- | ---------------------------------------------------------------------------------------- |
| スキーム制限  | **https のみ許可**。http/file/data/javascript 等は禁止                                   |
| IP 直指定禁止 | 127.0.0.1 / localhost / 169.254._ / 10._ / 172.16-31._ / 192.168._ 等は禁止（SSRF 対策） |
| 許可ドメイン  | 事前定義した許可ドメインリストのみ（TBD）                                                |
| 署名付き URL  | ファイルダウンロード系は署名付き URL（期限付き）運用を推奨（TBD）                        |

### 1.5 ポリモーフィック参照

| 方針             | 内容                                                                  |
| ---------------- | --------------------------------------------------------------------- |
| FK 制約          | DB で担保できないため、**アプリ層で存在チェック必須（例外なく）**     |
| 存在チェック条件 | 参照先が論理削除対応なら `deleted_at IS NULL` も含める                |
| 対象テーブル     | pack_items, user_entitlements, reports, user_blocks, terms_agreements |

### 1.6 通貨方針（MVP）

| 項目         | 方針                                                                            |
| ------------ | ------------------------------------------------------------------------------- |
| 対応通貨     | **JPY（日本円）のみ**                                                           |
| 金額単位     | 最小通貨単位（円）                                                              |
| 対象テーブル | packs.price, purchases.amount, creator_payouts.amount, payout_line_items.amount |
| 将来拡張     | 多通貨対応時は各テーブルに `currency` カラムを追加                              |

---

## 2. テーブル定義（全テーブル）

---

### m_age_groups

#### 概要

- ユーザーの年齢区分定義（u13/u18/adult 等）
- 参照用マスタデータ

#### カラム定義

| column     | type        | null | default           | constraints | description |
| ---------- | ----------- | ---- | ----------------- | ----------- | ----------- |
| id         | uuid        | NO   | gen_random_uuid() | PK          | 年齢区分 ID |
| code       | varchar(20) | NO   | —                 | UK          | 区分コード  |
| name       | varchar(50) | NO   | —                 | —           | 表示名      |
| sort_order | smallint    | NO   | 0                 | —           | 表示順      |
| created_at | timestamptz | NO   | now()             | —           | 作成日時    |
| updated_at | timestamptz | NO   | now()             | —           | 更新日時    |

#### インデックス一覧

| index_name            | type   | columns/expr | where | purpose      |
| --------------------- | ------ | ------------ | ----- | ------------ |
| m_age_groups_pkey     | PK     | (id)         | —     | 主キー       |
| m_age_groups_code_key | UNIQUE | (code)       | —     | コード一意性 |
| idx_m_age_groups_sort | INDEX  | (sort_order) | —     | 一覧ソート   |

#### バリデーションルール

- **code**: 必須、1-20 文字、英数字+アンダースコアのみ、一意 / コード識別子 / DB（NOT NULL, UK）、アプリ（正規表現）
- **name**: 必須、1-50 文字 / 表示名 / DB（NOT NULL）、アプリ（長さ）
- **sort_order**: 必須、0 以上の整数 / 表示順 / DB（NOT NULL, DEFAULT 0）、アプリ（範囲）

---

### m_relationship_stages

#### 概要

- 好感度に応じた関係性の段階定義（初対面 → 知り合い → 友達 → 仲良し → 恋人等）

#### カラム定義

| column     | type        | null | default           | constraints | description    |
| ---------- | ----------- | ---- | ----------------- | ----------- | -------------- |
| id         | uuid        | NO   | gen_random_uuid() | PK          | ステージ ID    |
| stage_code | varchar(30) | NO   | —                 | UK          | ステージコード |
| name       | varchar(50) | NO   | —                 | —           | 表示名         |
| threshold  | integer     | YES  | —                 | —           | 好感度閾値     |
| sort_order | smallint    | NO   | 0                 | —           | 表示順         |
| created_at | timestamptz | NO   | now()             | —           | 作成日時       |
| updated_at | timestamptz | NO   | now()             | —           | 更新日時       |

#### インデックス一覧

| index_name                           | type   | columns/expr | where | purpose      |
| ------------------------------------ | ------ | ------------ | ----- | ------------ |
| m_relationship_stages_pkey           | PK     | (id)         | —     | 主キー       |
| m_relationship_stages_stage_code_key | UNIQUE | (stage_code) | —     | コード一意性 |
| idx_m_relationship_stages_sort       | INDEX  | (sort_order) | —     | 一覧ソート   |

#### バリデーションルール

- **stage_code**: 必須、1-30 文字、英数字+アンダースコアのみ、一意 / ステージ識別子 / DB（NOT NULL, UK）、アプリ（正規表現）
- **name**: 必須、1-50 文字 / 表示名 / DB（NOT NULL）、アプリ（長さ）
- **threshold**: 任意、0 以上の整数 / 好感度閾値 / アプリ（範囲）
- **sort_order**: 必須、0 以上の整数 / 表示順 / DB（NOT NULL, DEFAULT 0）、アプリ（範囲）

---

### m_tags

#### 概要

- キャラクター/Pack 分類用のタグ（ジャンル、属性等）

#### カラム定義

| column     | type        | null | default           | constraints | description |
| ---------- | ----------- | ---- | ----------------- | ----------- | ----------- |
| id         | uuid        | NO   | gen_random_uuid() | PK          | タグ ID     |
| name       | varchar(50) | NO   | —                 | —           | タグ名      |
| category   | varchar(30) | NO   | 'general'         | —           | カテゴリ    |
| sort_order | smallint    | NO   | 0                 | —           | 表示順      |
| created_at | timestamptz | NO   | now()             | —           | 作成日時    |
| updated_at | timestamptz | NO   | now()             | —           | 更新日時    |

#### インデックス一覧

| index_name               | type   | columns/expr           | where | purpose                |
| ------------------------ | ------ | ---------------------- | ----- | ---------------------- |
| m_tags_pkey              | PK     | (id)                   | —     | 主キー                 |
| m_tags_category_name_key | UNIQUE | (category, name)       | —     | カテゴリ内タグ名一意性 |
| idx_m_tags_category_sort | INDEX  | (category, sort_order) | —     | カテゴリ別一覧ソート   |

#### バリデーションルール

- **name**: 必須、1-50 文字 / タグ名 / DB（NOT NULL）、アプリ（長さ）
- **category**: 必須、1-30 文字、デフォルト'general' / カテゴリ分類 / DB（NOT NULL, DEFAULT 'general'）、アプリ（長さ）
- **sort_order**: 必須、0 以上の整数 / 表示順 / DB（NOT NULL, DEFAULT 0）、アプリ（範囲）

---

### m_report_reasons

#### 概要

- 通報時に選択する理由の選択肢

#### カラム定義

| column      | type         | null | default           | constraints | description |
| ----------- | ------------ | ---- | ----------------- | ----------- | ----------- |
| id          | uuid         | NO   | gen_random_uuid() | PK          | 通報理由 ID |
| reason_code | varchar(30)  | NO   | —                 | UK          | 理由コード  |
| label       | varchar(100) | NO   | —                 | —           | 表示ラベル  |
| sort_order  | smallint     | NO   | 0                 | —           | 表示順      |
| created_at  | timestamptz  | NO   | now()             | —           | 作成日時    |
| updated_at  | timestamptz  | NO   | now()             | —           | 更新日時    |

#### インデックス一覧

| index_name                       | type   | columns/expr  | where | purpose      |
| -------------------------------- | ------ | ------------- | ----- | ------------ |
| m_report_reasons_pkey            | PK     | (id)          | —     | 主キー       |
| m_report_reasons_reason_code_key | UNIQUE | (reason_code) | —     | コード一意性 |
| idx_m_report_reasons_sort        | INDEX  | (sort_order)  | —     | 一覧ソート   |

#### バリデーションルール

- **reason_code**: 必須、1-30 文字、英数字+アンダースコアのみ、一意 / 理由コード識別子 / DB（NOT NULL, UK）、アプリ（正規表現）
- **label**: 必須、1-100 文字 / ユーザー向け表示ラベル / DB（NOT NULL）、アプリ（長さ）
- **sort_order**: 必須、0 以上の整数 / 表示順 / DB（NOT NULL, DEFAULT 0）、アプリ（範囲）

---

### m_event_types

#### 概要

- イベントの種別定義（1 回きり/周回可/状態変化等）

#### カラム定義

| column     | type        | null | default           | constraints | description     |
| ---------- | ----------- | ---- | ----------------- | ----------- | --------------- |
| id         | uuid        | NO   | gen_random_uuid() | PK          | イベント種別 ID |
| type_code  | varchar(30) | NO   | —                 | UK          | 種別コード      |
| name       | varchar(50) | NO   | —                 | —           | 表示名          |
| sort_order | smallint    | NO   | 0                 | —           | 表示順          |
| created_at | timestamptz | NO   | now()             | —           | 作成日時        |
| updated_at | timestamptz | NO   | now()             | —           | 更新日時        |

#### インデックス一覧

| index_name                  | type   | columns/expr | where | purpose      |
| --------------------------- | ------ | ------------ | ----- | ------------ |
| m_event_types_pkey          | PK     | (id)         | —     | 主キー       |
| m_event_types_type_code_key | UNIQUE | (type_code)  | —     | コード一意性 |
| idx_m_event_types_sort      | INDEX  | (sort_order) | —     | 一覧ソート   |

#### バリデーションルール

- **type_code**: 必須、1-30 文字、英数字+アンダースコアのみ、一意 / 種別コード識別子 / DB（NOT NULL, UK）、アプリ（正規表現）
- **name**: 必須、1-50 文字 / 表示名 / DB（NOT NULL）、アプリ（長さ）
- **sort_order**: 必須、0 以上の整数 / 表示順 / DB（NOT NULL, DEFAULT 0）、アプリ（範囲）

---

### m_voice_categories

#### 概要

- 音声素材の分類（相槌/挨拶/イベントセリフ等）

#### カラム定義

| column        | type        | null | default           | constraints | description     |
| ------------- | ----------- | ---- | ----------------- | ----------- | --------------- |
| id            | uuid        | NO   | gen_random_uuid() | PK          | 音声カテゴリ ID |
| category_code | varchar(30) | NO   | —                 | UK          | カテゴリコード  |
| name          | varchar(50) | NO   | —                 | —           | 表示名          |
| sort_order    | smallint    | NO   | 0                 | —           | 表示順          |
| created_at    | timestamptz | NO   | now()             | —           | 作成日時        |
| updated_at    | timestamptz | NO   | now()             | —           | 更新日時        |

#### インデックス一覧

| index_name                           | type   | columns/expr    | where | purpose      |
| ------------------------------------ | ------ | --------------- | ----- | ------------ |
| m_voice_categories_pkey              | PK     | (id)            | —     | 主キー       |
| m_voice_categories_category_code_key | UNIQUE | (category_code) | —     | コード一意性 |
| idx_m_voice_categories_sort          | INDEX  | (sort_order)    | —     | 一覧ソート   |

#### バリデーションルール

- **category_code**: 必須、1-30 文字、英数字+アンダースコアのみ、一意 / カテゴリコード識別子 / DB（NOT NULL, UK）、アプリ（正規表現）
- **name**: 必須、1-50 文字 / 表示名 / DB（NOT NULL）、アプリ（長さ）
- **sort_order**: 必須、0 以上の整数 / 表示順 / DB（NOT NULL, DEFAULT 0）、アプリ（範囲）

---

### m_flag_definitions

#### 概要

- イベント解放等に使う状態フラグの定義

#### カラム定義

| column      | type         | null | default           | constraints | description               |
| ----------- | ------------ | ---- | ----------------- | ----------- | ------------------------- |
| id          | uuid         | NO   | gen_random_uuid() | PK          | フラグ定義 ID             |
| flag_code   | varchar(50)  | NO   | —                 | UK          | フラグコード（FK 参照元） |
| description | varchar(200) | YES  | —                 | —           | フラグの説明              |
| created_at  | timestamptz  | NO   | now()             | —           | 作成日時                  |
| updated_at  | timestamptz  | NO   | now()             | —           | 更新日時                  |

#### インデックス一覧

| index_name                       | type   | columns/expr | where | purpose      |
| -------------------------------- | ------ | ------------ | ----- | ------------ |
| m_flag_definitions_pkey          | PK     | (id)         | —     | 主キー       |
| m_flag_definitions_flag_code_key | UNIQUE | (flag_code)  | —     | コード一意性 |

#### バリデーションルール

- **flag_code**: 必須、1-50 文字、英数字+アンダースコアのみ、一意 / フラグコード識別子、FK 参照元 / DB（NOT NULL, UK）、アプリ（正規表現）
- **description**: 任意、最大 200 文字 / フラグの説明 / アプリ（長さ）

---

### users

#### 概要

- エンドユーザーのアカウント情報

#### カラム定義

| column       | type         | null | default           | constraints               | description                                  |
| ------------ | ------------ | ---- | ----------------- | ------------------------- | -------------------------------------------- |
| id           | uuid         | NO   | gen_random_uuid() | PK                        | ユーザー ID                                  |
| email        | varchar(255) | NO   | —                 | —                         | メールアドレス（保存時に trim+小文字正規化） |
| display_name | varchar(50)  | NO   | —                 | —                         | 表示名                                       |
| age_group_id | uuid         | YES  | —                 | FK → m_age_groups(id)     | 年齢区分 ID                                  |
| status       | smallint     | NO   | 1                 | CHECK (status IN (1,2,3)) | ステータス（1:active/2:suspended/3:banned）  |
| created_at   | timestamptz  | NO   | now()             | —                         | 作成日時                                     |
| updated_at   | timestamptz  | NO   | now()             | —                         | 更新日時                                     |
| deleted_at   | timestamptz  | YES  | —                 | —                         | 論理削除日時                                 |

#### インデックス一覧

| index_name              | type         | columns/expr         | where              | purpose                                |
| ----------------------- | ------------ | -------------------- | ------------------ | -------------------------------------- |
| users_pkey              | PK           | (id)                 | —                  | 主キー                                 |
| users_email_active_uk   | UNIQUE INDEX | (lower(trim(email))) | deleted_at IS NULL | メールアドレス一意性（アクティブのみ） |
| idx_users_age_group     | INDEX        | (age_group_id)       | —                  | 年齢区分別集計                         |
| idx_users_status_active | INDEX        | (status)             | deleted_at IS NULL | ステータス別検索                       |

```sql
CREATE UNIQUE INDEX users_email_active_uk
  ON users (lower(trim(email)))
  WHERE deleted_at IS NULL;
```

#### バリデーションルール

- **email**: 必須、1-255 文字、RFC 5322 準拠、アクティブレコード内で一意、保存前に trim+小文字正規化 / ログイン識別子 / DB（NOT NULL, 部分 UNIQUE INDEX）、アプリ（形式チェック、trim、lowercase）
- **display_name**: 必須、1-50 文字、禁止語句を含まない / 表示名 / DB（NOT NULL）、アプリ（長さ、禁止語句フィルター）
- **age_group_id**: 任意、存在する m_age_groups.id を参照 / 年齢区分 / DB（FK）、アプリ（存在チェック）
- **status**: 必須、1/2/3 のいずれか / ユーザー状態 / DB（NOT NULL, DEFAULT 1, CHECK）、アプリ（enum 値チェック）

---

### creators

#### 概要

- キャラクター作成者のアカウント
- 1 ユーザー=0..1 クリエイター

#### カラム定義

| column       | type        | null | default           | constraints             | description                        |
| ------------ | ----------- | ---- | ----------------- | ----------------------- | ---------------------------------- |
| id           | uuid        | NO   | gen_random_uuid() | PK                      | クリエイター ID                    |
| user_id      | uuid        | NO   | —                 | FK → users(id)          | ユーザー ID                        |
| display_name | varchar(50) | NO   | —                 | —                       | クリエイター表示名                 |
| profile      | text        | YES  | —                 | —                       | プロフィール文                     |
| status       | smallint    | NO   | 1                 | CHECK (status IN (1,2)) | ステータス（1:active/2:suspended） |
| created_at   | timestamptz | NO   | now()             | —                       | 作成日時                           |
| updated_at   | timestamptz | NO   | now()             | —                       | 更新日時                           |
| deleted_at   | timestamptz | YES  | —                 | —                       | 論理削除日時                       |

#### インデックス一覧

| index_name                 | type         | columns/expr | where              | purpose                      |
| -------------------------- | ------------ | ------------ | ------------------ | ---------------------------- |
| creators_pkey              | PK           | (id)         | —                  | 主キー                       |
| creators_user_id_active_uk | UNIQUE INDEX | (user_id)    | deleted_at IS NULL | 1 ユーザー=0..1 クリエイター |
| idx_creators_status_active | INDEX        | (status)     | deleted_at IS NULL | ステータス別検索             |

```sql
CREATE UNIQUE INDEX creators_user_id_active_uk
  ON creators (user_id)
  WHERE deleted_at IS NULL;
```

#### バリデーションルール

- **user_id**: 必須、存在する users.id を参照、アクティブレコード内で一意 / 1 ユーザー=0..1 クリエイター / DB（NOT NULL, FK, 部分 UNIQUE INDEX）
- **display_name**: 必須、1-50 文字、禁止語句を含まない / クリエイター表示名 / DB（NOT NULL）、アプリ（長さ、禁止語句フィルター）
- **profile**: 任意、最大 5000 文字、禁止語句を含まない / プロフィール文 / アプリ（長さ、禁止語句フィルター）
- **status**: 必須、1/2 のいずれか / クリエイター状態 / DB（NOT NULL, DEFAULT 1, CHECK）、アプリ（enum 値チェック）

---

### admin_users

#### 概要

- 運営/モデレーターのアカウント

#### カラム定義

| column     | type         | null | default           | constraints                                     | description                                  |
| ---------- | ------------ | ---- | ----------------- | ----------------------------------------------- | -------------------------------------------- |
| id         | uuid         | NO   | gen_random_uuid() | PK                                              | 運営ユーザー ID                              |
| email      | varchar(255) | NO   | —                 | —                                               | メールアドレス（保存時に trim+小文字正規化） |
| name       | varchar(50)  | NO   | —                 | —                                               | 氏名                                         |
| role       | varchar(30)  | NO   | —                 | CHECK (role IN ('admin','moderator','support')) | 権限ロール                                   |
| created_at | timestamptz  | NO   | now()             | —                                               | 作成日時                                     |
| updated_at | timestamptz  | NO   | now()             | —                                               | 更新日時                                     |
| deleted_at | timestamptz  | YES  | —                 | —                                               | 論理削除日時                                 |

#### インデックス一覧

| index_name                  | type         | columns/expr         | where              | purpose              |
| --------------------------- | ------------ | -------------------- | ------------------ | -------------------- |
| admin_users_pkey            | PK           | (id)                 | —                  | 主キー               |
| admin_users_email_active_uk | UNIQUE INDEX | (lower(trim(email))) | deleted_at IS NULL | メールアドレス一意性 |
| idx_admin_users_role_active | INDEX        | (role)               | deleted_at IS NULL | ロール別検索         |

```sql
CREATE UNIQUE INDEX admin_users_email_active_uk
  ON admin_users (lower(trim(email)))
  WHERE deleted_at IS NULL;
```

#### バリデーションルール

- **email**: 必須、1-255 文字、RFC 5322 準拠、アクティブレコード内で一意、保存前に trim+小文字正規化 / ログイン識別子 / DB（NOT NULL, 部分 UNIQUE INDEX）、アプリ（形式チェック、trim、lowercase）
- **name**: 必須、1-50 文字 / 運営者氏名 / DB（NOT NULL）、アプリ（長さ）
- **role**: 必須、許可値：admin/moderator/support / 権限ロール / DB（NOT NULL, CHECK）、アプリ（enum 値チェック）

---

### characters

#### 概要

- クリエイターが作成したキャラクターの基本情報
- 単体販売せず必ず Pack 経由で販売

#### カラム定義

| column      | type         | null | default           | constraints               | description                                   |
| ----------- | ------------ | ---- | ----------------- | ------------------------- | --------------------------------------------- |
| id          | uuid         | NO   | gen_random_uuid() | PK                        | キャラクター ID                               |
| creator_id  | uuid         | NO   | —                 | FK → creators(id)         | 作成者 ID                                     |
| name        | varchar(50)  | NO   | —                 | —                         | キャラクター名                                |
| description | text         | YES  | —                 | —                         | 説明文                                        |
| image_url   | varchar(500) | YES  | —                 | —                         | 画像 URL                                      |
| status      | smallint     | NO   | 1                 | CHECK (status IN (1,2,3)) | ステータス（1:draft/2:published/3:suspended） |
| created_at  | timestamptz  | NO   | now()             | —                         | 作成日時                                      |
| updated_at  | timestamptz  | NO   | now()             | —                         | 更新日時                                      |
| deleted_at  | timestamptz  | YES  | —                 | —                         | 論理削除日時                                  |

#### インデックス一覧

| index_name                    | type  | columns/expr                  | where              | purpose                      |
| ----------------------------- | ----- | ----------------------------- | ------------------ | ---------------------------- |
| characters_pkey               | PK    | (id)                          | —                  | 主キー                       |
| idx_characters_creator_active | INDEX | (creator_id, created_at DESC) | deleted_at IS NULL | クリエイター別一覧（新着順） |
| idx_characters_status_active  | INDEX | (status, created_at DESC)     | deleted_at IS NULL | マーケット一覧（新着順）     |

#### バリデーションルール

- **creator_id**: 必須、存在する creators.id を参照 / キャラクター作成者 / DB（NOT NULL, FK）
- **name**: 必須、1-50 文字、禁止語句を含まない / キャラクター名 / DB（NOT NULL）、アプリ（長さ、禁止語句フィルター）
- **description**: 任意、最大 5000 文字、禁止語句を含まない / 説明文 / アプリ（長さ、禁止語句フィルター）
- **image_url**: 任意、最大 500 文字、https のみ、許可ドメイン、IP 直指定禁止 / 画像 URL / アプリ（URL 共通ルール）
- **status**: 必須、1/2/3 のいずれか / 公開状態 / DB（NOT NULL, DEFAULT 1, CHECK）、アプリ（enum 値チェック）

---

### character_personalities

#### 概要

- キャラクターの性格・口調・世界観等の設定
- 1 キャラクター=1 人格設定（1:1）

#### カラム定義

| column           | type        | null | default           | constraints             | description                 |
| ---------------- | ----------- | ---- | ----------------- | ----------------------- | --------------------------- |
| id               | uuid        | NO   | gen_random_uuid() | PK                      | 人格設定 ID                 |
| character_id     | uuid        | NO   | —                 | FK → characters(id), UK | キャラクター ID（1:1）      |
| personality_data | jsonb       | NO   | —                 | —                       | 性格・口調・世界観等の JSON |
| created_at       | timestamptz | NO   | now()             | —                       | 作成日時                    |
| updated_at       | timestamptz | NO   | now()             | —                       | 更新日時                    |

#### インデックス一覧

| index_name                               | type   | columns/expr   | where | purpose      |
| ---------------------------------------- | ------ | -------------- | ----- | ------------ |
| character_personalities_pkey             | PK     | (id)           | —     | 主キー       |
| character_personalities_character_id_key | UNIQUE | (character_id) | —     | 1:1 関係担保 |

#### バリデーションルール

- **character_id**: 必須、存在する characters.id を参照、一意 / 1 キャラ=1 人格設定 / DB（NOT NULL, FK, UK）
- **personality_data**: 必須、有効な JSON 形式、必須キーを含む（TBD） / 性格・口調等の設定 / DB（NOT NULL）、アプリ（JSON スキーマ検証）

---

### packs

#### 概要

- Persona Pack / Scenario Pack 等の販売単位
- クリエイターが作成・所有する

#### カラム定義

| column      | type         | null | default           | constraints                                                                   | description                                   |
| ----------- | ------------ | ---- | ----------------- | ----------------------------------------------------------------------------- | --------------------------------------------- |
| id          | uuid         | NO   | gen_random_uuid() | PK                                                                            | PackID                                        |
| creator_id  | uuid         | NO   | —                 | FK → creators(id)                                                             | 作成者 ID（所有者）                           |
| pack_type   | varchar(30)  | NO   | —                 | CHECK (pack_type IN ('persona','scenario'))                                   | Pack 種別                                     |
| name        | varchar(100) | NO   | —                 | —                                                                             | Pack 名                                       |
| description | text         | YES  | —                 | —                                                                             | 説明文                                        |
| price       | integer      | YES  | —                 | CHECK (price IS NULL OR price >= 0), CHECK (status <> 2 OR price IS NOT NULL) | 価格（最小通貨単位・JPY、0=無料）             |
| status      | smallint     | NO   | 1                 | CHECK (status IN (1,2,3))                                                     | ステータス（1:draft/2:published/3:suspended） |
| created_at  | timestamptz  | NO   | now()             | —                                                                             | 作成日時                                      |
| updated_at  | timestamptz  | NO   | now()             | —                                                                             | 更新日時                                      |
| deleted_at  | timestamptz  | YES  | —                 | —                                                                             | 論理削除日時                                  |

#### インデックス一覧

| index_name                   | type  | columns/expr                         | where              | purpose                  |
| ---------------------------- | ----- | ------------------------------------ | ------------------ | ------------------------ |
| packs_pkey                   | PK    | (id)                                 | —                  | 主キー                   |
| idx_packs_creator_active     | INDEX | (creator_id, created_at DESC)        | deleted_at IS NULL | クリエイター別 Pack 一覧 |
| idx_packs_type_status_active | INDEX | (pack_type, status, created_at DESC) | deleted_at IS NULL | マーケット一覧           |

```sql
-- published時にpriceが必須であることをDBで担保
ALTER TABLE packs ADD CONSTRAINT packs_published_requires_price
  CHECK (status <> 2 OR price IS NOT NULL);
```

#### バリデーションルール

- **creator_id**: 必須、存在する creators.id を参照 / Pack 所有者 / DB（NOT NULL, FK）
- **pack_type**: 必須、許可値：persona/scenario / Pack 種別 / DB（NOT NULL, CHECK）、アプリ（enum 値チェック）
- **name**: 必須、1-100 文字、禁止語句を含まない / Pack 名 / DB（NOT NULL）、アプリ（長さ、禁止語句フィルター）
- **description**: 任意、最大 5000 文字、禁止語句を含まない / 説明文 / アプリ（長さ、禁止語句フィルター）
- **price**: status=2(published)時は必須、0 以上の整数（0=無料を許可） / 価格 / DB（CHECK (price IS NULL OR price >= 0), CHECK (status <> 2 OR price IS NOT NULL)）、アプリ（範囲チェック）
- **status**: 必須、1/2/3 のいずれか / 公開状態 / DB（NOT NULL, DEFAULT 1, CHECK）、アプリ（enum 値チェック）

**条件付きルール**:

- `status=2(published)` 時: `price` は必須（DB CHECK で担保）、かつ `pack_items` が 1 件以上存在すること（アプリ層）

---

### pack_items

#### 概要

- Pack に含まれるコンテンツ
- ポリモーフィック参照（item_type + item_id）

#### カラム定義

| column     | type        | null | default           | constraints                                             | description                     |
| ---------- | ----------- | ---- | ----------------- | ------------------------------------------------------- | ------------------------------- |
| id         | uuid        | NO   | gen_random_uuid() | PK                                                      | Pack 構成 ID                    |
| pack_id    | uuid        | NO   | —                 | FK → packs(id)                                          | PackID                          |
| item_type  | varchar(30) | NO   | —                 | CHECK (item_type IN ('character','event','voice_pack')) | アイテム種別                    |
| item_id    | uuid        | NO   | —                 | —                                                       | アイテム ID（ポリモーフィック） |
| created_at | timestamptz | NO   | now()             | —                                                       | 作成日時                        |
| updated_at | timestamptz | NO   | now()             | —                                                       | 更新日時                        |
| deleted_at | timestamptz | YES  | —                 | —                                                       | 論理削除日時                    |

#### インデックス一覧

| index_name            | type         | columns/expr                  | where              | purpose                |
| --------------------- | ------------ | ----------------------------- | ------------------ | ---------------------- |
| pack_items_pkey       | PK           | (id)                          | —                  | 主キー                 |
| pack_items_active_uk  | UNIQUE INDEX | (pack_id, item_type, item_id) | deleted_at IS NULL | Pack 内重複防止        |
| idx_pack_items_target | INDEX        | (item_type, item_id)          | —                  | ポリモーフィック逆引き |

```sql
CREATE UNIQUE INDEX pack_items_active_uk
  ON pack_items (pack_id, item_type, item_id)
  WHERE deleted_at IS NULL;
```

#### バリデーションルール

- **pack_id**: 必須、存在する packs.id を参照 / Pack 所属 / DB（NOT NULL, FK）
- **item_type**: 必須、許可値：character/event/voice_pack / アイテム種別 / DB（NOT NULL, CHECK）、アプリ（enum 値チェック）
- **item_id**: 必須、UUID 形式、item_type に応じた存在チェック必須かつ deleted_at IS NULL であること / ポリモーフィック参照先 / アプリ（存在チェック＋論理削除チェック必須）

**ポリモーフィック参照先**:
| item_type | 参照先テーブル | 存在チェック条件 |
|-----------|---------------|-----------------|
| character | characters | `id = :item_id AND deleted_at IS NULL` |
| event | events | `id = :item_id AND deleted_at IS NULL` |
| voice_pack | voice_packs | `id = :item_id AND deleted_at IS NULL` |

---

### character_tags

#### 概要

- キャラクターとタグの紐付け（多対多）

#### カラム定義

| column       | type        | null | default           | constraints         | description     |
| ------------ | ----------- | ---- | ----------------- | ------------------- | --------------- |
| id           | uuid        | NO   | gen_random_uuid() | PK                  | 中間テーブル ID |
| character_id | uuid        | NO   | —                 | FK → characters(id) | キャラクター ID |
| tag_id       | uuid        | NO   | —                 | FK → m_tags(id)     | タグ ID         |
| created_at   | timestamptz | NO   | now()             | —                   | 作成日時        |
| deleted_at   | timestamptz | YES  | —                 | —                   | 論理削除日時    |

#### インデックス一覧

| index_name               | type         | columns/expr           | where              | purpose                |
| ------------------------ | ------------ | ---------------------- | ------------------ | ---------------------- |
| character_tags_pkey      | PK           | (id)                   | —                  | 主キー                 |
| character_tags_active_uk | UNIQUE INDEX | (character_id, tag_id) | deleted_at IS NULL | タグ重複付与防止       |
| idx_character_tags_tag   | INDEX        | (tag_id)               | —                  | タグ別キャラクター検索 |

```sql
CREATE UNIQUE INDEX character_tags_active_uk
  ON character_tags (character_id, tag_id)
  WHERE deleted_at IS NULL;
```

#### バリデーションルール

- **character_id**: 必須、存在する characters.id を参照 / キャラクター特定 / DB（NOT NULL, FK）
- **tag_id**: 必須、存在する m_tags.id を参照 / タグ特定 / DB（NOT NULL, FK）

---

### pack_tags

#### 概要

- Pack とタグの紐付け（多対多）

#### カラム定義

| column     | type        | null | default           | constraints     | description     |
| ---------- | ----------- | ---- | ----------------- | --------------- | --------------- |
| id         | uuid        | NO   | gen_random_uuid() | PK              | 中間テーブル ID |
| pack_id    | uuid        | NO   | —                 | FK → packs(id)  | PackID          |
| tag_id     | uuid        | NO   | —                 | FK → m_tags(id) | タグ ID         |
| created_at | timestamptz | NO   | now()             | —               | 作成日時        |
| deleted_at | timestamptz | YES  | —                 | —               | 論理削除日時    |

#### インデックス一覧

| index_name          | type         | columns/expr      | where              | purpose          |
| ------------------- | ------------ | ----------------- | ------------------ | ---------------- |
| pack_tags_pkey      | PK           | (id)              | —                  | 主キー           |
| pack_tags_active_uk | UNIQUE INDEX | (pack_id, tag_id) | deleted_at IS NULL | タグ重複付与防止 |
| idx_pack_tags_tag   | INDEX        | (tag_id)          | —                  | タグ別 Pack 検索 |

```sql
CREATE UNIQUE INDEX pack_tags_active_uk
  ON pack_tags (pack_id, tag_id)
  WHERE deleted_at IS NULL;
```

#### バリデーションルール

- **pack_id**: 必須、存在する packs.id を参照 / Pack 特定 / DB（NOT NULL, FK）
- **tag_id**: 必須、存在する m_tags.id を参照 / タグ特定 / DB（NOT NULL, FK）

---

### user_creator_follows

#### 概要

- ユーザーによるクリエイターのフォロー

#### カラム定義

| column     | type        | null | default           | constraints       | description                   |
| ---------- | ----------- | ---- | ----------------- | ----------------- | ----------------------------- |
| id         | uuid        | NO   | gen_random_uuid() | PK                | フォロー ID                   |
| user_id    | uuid        | NO   | —                 | FK → users(id)    | ユーザー ID                   |
| creator_id | uuid        | NO   | —                 | FK → creators(id) | クリエイター ID               |
| created_at | timestamptz | NO   | now()             | —                 | 作成日時                      |
| deleted_at | timestamptz | YES  | —                 | —                 | 論理削除日時（=フォロー解除） |

#### インデックス一覧

| index_name                       | type         | columns/expr          | where              | purpose                |
| -------------------------------- | ------------ | --------------------- | ------------------ | ---------------------- |
| user_creator_follows_pkey        | PK           | (id)                  | —                  | 主キー                 |
| user_creator_follows_active_uk   | UNIQUE INDEX | (user_id, creator_id) | deleted_at IS NULL | 重複フォロー防止       |
| idx_user_creator_follows_creator | INDEX        | (creator_id)          | —                  | フォロワー一覧・数取得 |

```sql
CREATE UNIQUE INDEX user_creator_follows_active_uk
  ON user_creator_follows (user_id, creator_id)
  WHERE deleted_at IS NULL;
```

#### バリデーションルール

- **user_id**: 必須、存在する users.id を参照 / フォロー元ユーザー / DB（NOT NULL, FK）
- **creator_id**: 必須、存在する creators.id を参照 / フォロー先クリエイター / DB（NOT NULL, FK）
- **ビジネスルール**: 自分自身（user_id→creators.user_id）のフォロー禁止 → アプリ側でチェック

---

### user_favorites

#### 概要

- ユーザーがお気に入り登録したキャラクター

#### カラム定義

| column       | type        | null | default           | constraints         | description                     |
| ------------ | ----------- | ---- | ----------------- | ------------------- | ------------------------------- |
| id           | uuid        | NO   | gen_random_uuid() | PK                  | お気に入り ID                   |
| user_id      | uuid        | NO   | —                 | FK → users(id)      | ユーザー ID                     |
| character_id | uuid        | NO   | —                 | FK → characters(id) | キャラクター ID                 |
| created_at   | timestamptz | NO   | now()             | —                   | 作成日時                        |
| deleted_at   | timestamptz | YES  | —                 | —                   | 論理削除日時（=お気に入り解除） |

#### インデックス一覧

| index_name                      | type         | columns/expr               | where              | purpose                  |
| ------------------------------- | ------------ | -------------------------- | ------------------ | ------------------------ |
| user_favorites_pkey             | PK           | (id)                       | —                  | 主キー                   |
| user_favorites_active_uk        | UNIQUE INDEX | (user_id, character_id)    | deleted_at IS NULL | 重複お気に入り防止       |
| idx_user_favorites_user_created | INDEX        | (user_id, created_at DESC) | —                  | お気に入り一覧（新着順） |
| idx_user_favorites_character    | INDEX        | (character_id)             | —                  | お気に入り数集計         |

```sql
CREATE UNIQUE INDEX user_favorites_active_uk
  ON user_favorites (user_id, character_id)
  WHERE deleted_at IS NULL;
```

#### バリデーションルール

- **user_id**: 必須、存在する users.id を参照 / お気に入り登録者 / DB（NOT NULL, FK）
- **character_id**: 必須、存在する characters.id を参照 / お気に入り対象 / DB（NOT NULL, FK）

---

### purchases

#### 概要

- 決済記録（Source of Truth）
- 返金時は user_entitlements を revoke
- **論理削除の例外テーブル**（会計証跡として永続保存）

#### カラム定義

| column           | type         | null | default           | constraints                                             | description                                    |
| ---------------- | ------------ | ---- | ----------------- | ------------------------------------------------------- | ---------------------------------------------- |
| id               | uuid         | NO   | gen_random_uuid() | PK                                                      | 購入 ID                                        |
| user_id          | uuid         | NO   | —                 | FK → users(id)                                          | ユーザー ID                                    |
| payment_provider | varchar(30)  | NO   | —                 | CHECK (payment_provider IN ('stripe','apple','google')) | 決済プロバイダ                                 |
| payment_id       | varchar(255) | NO   | —                 | —                                                       | 外部決済 ID                                    |
| amount           | integer      | NO   | —                 | CHECK (amount >= 0)                                     | 金額（最小通貨単位・JPY）                      |
| currency         | varchar(3)   | NO   | 'JPY'             | CHECK (currency = 'JPY')                                | 通貨コード（MVP: JPY 固定）                    |
| status           | smallint     | NO   | 1                 | CHECK (status IN (1,2,3)), CHECK (状態遷移整合)         | ステータス（1:pending/2:completed/3:refunded） |
| purchased_at     | timestamptz  | YES  | —                 | CHECK (状態遷移整合)                                    | 購入確定日時                                   |
| refunded_at      | timestamptz  | YES  | —                 | CHECK (状態遷移整合)                                    | 返金処理日時                                   |
| created_at       | timestamptz  | NO   | now()             | —                                                       | 作成日時                                       |
| updated_at       | timestamptz  | NO   | now()             | —                                                       | 更新日時                                       |

```sql
-- status と日時カラムの整合性をDBで担保
ALTER TABLE purchases ADD CONSTRAINT purchases_status_dates
  CHECK (
    -- pending(1)の場合: purchased_at/refunded_at は両方NULL
    (status = 1 AND purchased_at IS NULL AND refunded_at IS NULL)
    OR
    -- completed(2)の場合: purchased_at必須、refunded_atはNULL
    (status = 2 AND purchased_at IS NOT NULL AND refunded_at IS NULL)
    OR
    -- refunded(3)の場合: purchased_at/refunded_at 両方必須
    (status = 3 AND purchased_at IS NOT NULL AND refunded_at IS NOT NULL)
  );
```

#### インデックス一覧

| index_name                 | type   | columns/expr                   | where | purpose          |
| -------------------------- | ------ | ------------------------------ | ----- | ---------------- |
| purchases_pkey             | PK     | (id)                           | —     | 主キー           |
| purchases_payment_uk       | UNIQUE | (payment_provider, payment_id) | —     | 冪等性担保       |
| idx_purchases_user_created | INDEX  | (user_id, created_at DESC)     | —     | 購入履歴一覧     |
| idx_purchases_status       | INDEX  | (status, purchased_at DESC)    | —     | ステータス別一覧 |

#### バリデーションルール

- **user_id**: 必須、存在する users.id を参照 / 購入者 / DB（NOT NULL, FK）
- **payment_provider**: 必須、許可値：stripe/apple/google / 決済プロバイダ / DB（NOT NULL, CHECK）、アプリ（enum 値チェック）
- **payment_id**: 必須、1-255 文字 / 外部決済 ID / DB（NOT NULL）、アプリ（形式チェック）
- **amount**: 必須、0 以上の整数 / 金額 / DB（NOT NULL, CHECK (amount >= 0)）、アプリ（範囲チェック）
- **currency**: 必須、JPY 固定（MVP） / 通貨コード / DB（NOT NULL, DEFAULT 'JPY', CHECK (currency = 'JPY')）
- **status**: 必須、1/2/3 のいずれか / 購入状態 / DB（NOT NULL, DEFAULT 1, CHECK）、アプリ（enum 値チェック）
- **purchased_at**: status IN (2,3) 時は必須 / 購入確定日時 / DB（CHECK 状態遷移整合）、アプリ（状態遷移時に自動セット）
- **refunded_at**: status=3(refunded) 時は必須、それ以外は NULL / 返金処理日時 / DB（CHECK 状態遷移整合）、アプリ（返金時に自動セット）

**状態遷移ルール（DB CHECK で担保）**:
| status | purchased_at | refunded_at |
|--------|--------------|-------------|
| 1 (pending) | NULL | NULL |
| 2 (completed) | NOT NULL | NULL |
| 3 (refunded) | NOT NULL | NOT NULL |

---

### user_entitlements

#### 概要

- ユーザーが保持する利用権（購入/無料付与/復元）

#### カラム定義

| column             | type        | null | default           | constraints                          | description                  |
| ------------------ | ----------- | ---- | ----------------- | ------------------------------------ | ---------------------------- |
| id                 | uuid        | NO   | gen_random_uuid() | PK                                   | 利用権 ID                    |
| user_id            | uuid        | NO   | —                 | FK → users(id)                       | ユーザー ID                  |
| entitlement_type   | varchar(30) | NO   | —                 | CHECK (entitlement_type IN ('pack')) | 利用権種別                   |
| entitlement_id     | uuid        | NO   | —                 | —                                    | 対象 ID（ポリモーフィック）  |
| source_purchase_id | uuid        | YES  | —                 | FK → purchases(id)                   | 購入元 ID（無料付与時 NULL） |
| revoked_at         | timestamptz | YES  | —                 | —                                    | 取り消し日時                 |
| created_at         | timestamptz | NO   | now()             | —                                    | 作成日時                     |
| updated_at         | timestamptz | NO   | now()             | —                                    | 更新日時                     |

#### インデックス一覧

| index_name                     | type         | columns/expr                                | where              | purpose                |
| ------------------------------ | ------------ | ------------------------------------------- | ------------------ | ---------------------- |
| user_entitlements_pkey         | PK           | (id)                                        | —                  | 主キー                 |
| user_entitlements_active_uk    | UNIQUE INDEX | (user_id, entitlement_type, entitlement_id) | revoked_at IS NULL | 有効な利用権の重複防止 |
| idx_user_entitlements_user     | INDEX        | (user_id)                                   | —                  | ユーザーの利用権一覧   |
| idx_user_entitlements_purchase | INDEX        | (source_purchase_id)                        | —                  | 購入元逆引き           |
| idx_user_entitlements_target   | INDEX        | (entitlement_type, entitlement_id)          | —                  | ポリモーフィック逆引き |

```sql
CREATE UNIQUE INDEX user_entitlements_active_uk
  ON user_entitlements (user_id, entitlement_type, entitlement_id)
  WHERE revoked_at IS NULL;
```

#### バリデーションルール

- **user_id**: 必須、存在する users.id を参照 / 利用権保持者 / DB（NOT NULL, FK）
- **entitlement_type**: 必須、許可値：pack / 利用権種別 / DB（NOT NULL, CHECK）、アプリ（enum 値チェック）
- **entitlement_id**: 必須、UUID 形式、entitlement_type に応じた存在チェック必須かつ status=2（published）であること / ポリモーフィック参照先 / アプリ（存在チェック＋ステータスチェック必須）
- **source_purchase_id**: 任意、存在する purchases.id を参照 / 購入元追跡 / DB（FK）
- **revoked_at**: ユーザー入力禁止、取り消し時のみサーバー側で付与 / 取り消し日時 / アプリ（revoke API 経由のみ）

**ポリモーフィック参照先**:
| entitlement_type | 参照先テーブル | 存在チェック条件 |
|------------------|---------------|-----------------|
| pack | packs | `id = :entitlement_id AND deleted_at IS NULL AND status = 2` |

---

### user_ticket_balances

#### 概要

- ユーザーのチケット/クレジット残高（キャッシュ）
- ticket_transactions から再計算可能

#### カラム定義

| column     | type        | null | default           | constraints          | description  |
| ---------- | ----------- | ---- | ----------------- | -------------------- | ------------ |
| id         | uuid        | NO   | gen_random_uuid() | PK                   | 残高 ID      |
| user_id    | uuid        | NO   | —                 | FK → users(id), UK   | ユーザー ID  |
| balance    | integer     | NO   | 0                 | CHECK (balance >= 0) | チケット残高 |
| created_at | timestamptz | NO   | now()             | —                    | 作成日時     |
| updated_at | timestamptz | NO   | now()             | —                    | 更新日時     |

#### インデックス一覧

| index_name                       | type   | columns/expr | where | purpose           |
| -------------------------------- | ------ | ------------ | ----- | ----------------- |
| user_ticket_balances_pkey        | PK     | (id)         | —     | 主キー            |
| user_ticket_balances_user_id_key | UNIQUE | (user_id)    | —     | 1 ユーザー 1 残高 |

#### バリデーションルール

- **user_id**: 必須、存在する users.id を参照、一意 / 1 ユーザー 1 残高 / DB（NOT NULL, FK, UK）
- **balance**: 必須、0 以上の整数 / 残高は負にならない / DB（NOT NULL, DEFAULT 0, CHECK）

---

### ticket_transactions

#### 概要

- チケットの購入・消費履歴（Source of Truth）
- **論理削除の例外テーブル**（会計証跡として永続保存）
- **updated_at を持たない**（イミュータブルなログ）
- **amount は符号付き**（金額系 CHECK 制約 `>= 0` の例外）

#### カラム定義

| column           | type        | null | default           | constraints                                                         | description                                    |
| ---------------- | ----------- | ---- | ----------------- | ------------------------------------------------------------------- | ---------------------------------------------- |
| id               | uuid        | NO   | gen_random_uuid() | PK                                                                  | 取引 ID                                        |
| user_id          | uuid        | NO   | —                 | FK → users(id)                                                      | ユーザー ID                                    |
| transaction_type | varchar(20) | NO   | —                 | CHECK (transaction_type IN ('purchase','consume','refund','grant')) | 取引種別                                       |
| amount           | integer     | NO   | —                 | CHECK (符号整合)                                                    | 増減量（purchase/grant/refund:正、consume:負） |
| reference_id     | uuid        | YES  | —                 | —                                                                   | 参照 ID（購入 ID 等）                          |
| created_at       | timestamptz | NO   | now()             | —                                                                   | 作成日時                                       |

```sql
-- transaction_type と amount の符号整合をDBで担保
ALTER TABLE ticket_transactions ADD CONSTRAINT ticket_transactions_amount_sign
  CHECK (
    (transaction_type IN ('purchase', 'grant', 'refund') AND amount > 0)
    OR
    (transaction_type = 'consume' AND amount < 0)
  );
```

#### インデックス一覧

| index_name                           | type  | columns/expr               | where | purpose      |
| ------------------------------------ | ----- | -------------------------- | ----- | ------------ |
| ticket_transactions_pkey             | PK    | (id)                       | —     | 主キー       |
| idx_ticket_transactions_user_created | INDEX | (user_id, created_at DESC) | —     | 取引履歴一覧 |

#### バリデーションルール

- **user_id**: 必須、存在する users.id を参照 / 取引対象ユーザー / DB（NOT NULL, FK）
- **transaction_type**: 必須、許可値：purchase/consume/refund/grant / 取引種別 / DB（NOT NULL, CHECK）、アプリ（enum 値チェック）
- **amount**: 必須、整数（purchase/grant/refund:正、consume:負） / 増減量 / DB（NOT NULL, CHECK 符号整合）、アプリ（transaction_type との整合性チェック）
- **reference_id**: 任意、UUID 形式 / 関連購入等の追跡 / アプリ（存在チェック）

---

### payout_accounts

#### 概要

- クリエイターの振込先情報

#### カラム定義

| column     | type        | null | default           | constraints       | description                |
| ---------- | ----------- | ---- | ----------------- | ----------------- | -------------------------- |
| id         | uuid        | NO   | gen_random_uuid() | PK                | 振込口座 ID                |
| creator_id | uuid        | NO   | —                 | FK → creators(id) | クリエイター ID            |
| is_default | boolean     | NO   | false             | —                 | デフォルト口座フラグ       |
| bank_info  | jsonb       | NO   | —                 | —                 | 銀行口座情報（暗号化推奨） |
| created_at | timestamptz | NO   | now()             | —                 | 作成日時                   |
| updated_at | timestamptz | NO   | now()             | —                 | 更新日時                   |
| deleted_at | timestamptz | YES  | —                 | —                 | 論理削除日時               |

#### インデックス一覧

| index_name                         | type         | columns/expr | where                                    | purpose                  |
| ---------------------------------- | ------------ | ------------ | ---------------------------------------- | ------------------------ |
| payout_accounts_pkey               | PK           | (id)         | —                                        | 主キー                   |
| payout_accounts_default_uk         | UNIQUE INDEX | (creator_id) | is_default = true AND deleted_at IS NULL | デフォルト口座の重複防止 |
| idx_payout_accounts_creator_active | INDEX        | (creator_id) | deleted_at IS NULL                       | 有効口座一覧             |

```sql
CREATE UNIQUE INDEX payout_accounts_default_uk
  ON payout_accounts (creator_id)
  WHERE is_default = true AND deleted_at IS NULL;
```

#### バリデーションルール

- **creator_id**: 必須、存在する creators.id を参照 / 口座所有者 / DB（NOT NULL, FK）
- **is_default**: 必須、true/false / デフォルト口座フラグ / DB（NOT NULL, DEFAULT false）
- **bank_info**: 必須、有効な JSON 形式、必須キーを含む（TBD） / 振込先情報 / DB（NOT NULL）、アプリ（JSON スキーマ検証）

---

### creator_payouts

#### 概要

- クリエイターへの収益分配記録

#### カラム定義

| column            | type        | null | default           | constraints               | description                                      |
| ----------------- | ----------- | ---- | ----------------- | ------------------------- | ------------------------------------------------ |
| id                | uuid        | NO   | gen_random_uuid() | PK                        | 支払い ID                                        |
| creator_id        | uuid        | NO   | —                 | FK → creators(id)         | クリエイター ID                                  |
| payout_account_id | uuid        | YES  | —                 | FK → payout_accounts(id)  | 振込口座 ID                                      |
| period_start      | date        | NO   | —                 | —                         | 対象期間開始                                     |
| period_end        | date        | NO   | —                 | —                         | 対象期間終了                                     |
| amount            | integer     | NO   | —                 | CHECK (amount >= 0)       | 支払い金額                                       |
| status            | smallint    | NO   | 1                 | CHECK (status IN (1,2,3)) | ステータス（1:pending/2:processing/3:completed） |
| paid_at           | timestamptz | YES  | —                 | —                         | 支払い日時                                       |
| created_at        | timestamptz | NO   | now()             | —                         | 作成日時                                         |
| updated_at        | timestamptz | NO   | now()             | —                         | 更新日時                                         |

#### インデックス一覧

| index_name                         | type  | columns/expr                    | where | purpose          |
| ---------------------------------- | ----- | ------------------------------- | ----- | ---------------- |
| creator_payouts_pkey               | PK    | (id)                            | —     | 主キー           |
| idx_creator_payouts_creator_period | INDEX | (creator_id, period_start DESC) | —     | 支払い履歴       |
| idx_creator_payouts_account        | INDEX | (payout_account_id)             | —     | 口座別支払い履歴 |
| idx_creator_payouts_status         | INDEX | (status)                        | —     | ステータス別一覧 |

#### バリデーションルール

- **creator_id**: 必須、存在する creators.id を参照 / 支払い対象 / DB（NOT NULL, FK）
- **payout_account_id**: 任意、存在する payout_accounts.id を参照 / 振込先口座 / DB（FK）
- **period_start**: 必須、有効な日付、period_end 以前 / 対象期間開始 / DB（NOT NULL）、アプリ（範囲チェック）
- **period_end**: 必須、有効な日付、period_start 以後 / 対象期間終了 / DB（NOT NULL）、アプリ（範囲チェック）
- **amount**: 必須、0 以上の整数 / 支払い金額 / DB（NOT NULL, CHECK (amount >= 0)）、アプリ（範囲チェック）
- **status**: 必須、1/2/3 のいずれか / 支払い状態 / DB（NOT NULL, DEFAULT 1, CHECK）、アプリ（enum 値チェック）
- **paid_at**: 任意、完了時にセット / 支払い日時 / アプリ（完了時に自動セット）

---

### payout_line_items

#### 概要

- 分配対象の売上明細
- **updated_at を持たない**（明細記録のみ）

#### カラム定義

| column      | type        | null | default           | constraints              | description |
| ----------- | ----------- | ---- | ----------------- | ------------------------ | ----------- |
| id          | uuid        | NO   | gen_random_uuid() | PK                       | 明細 ID     |
| payout_id   | uuid        | NO   | —                 | FK → creator_payouts(id) | 支払い ID   |
| purchase_id | uuid        | YES  | —                 | FK → purchases(id)       | 購入 ID     |
| amount      | integer     | NO   | —                 | CHECK (amount >= 0)      | 明細金額    |
| created_at  | timestamptz | NO   | now()             | —                        | 作成日時    |

#### インデックス一覧

| index_name                     | type  | columns/expr  | where | purpose        |
| ------------------------------ | ----- | ------------- | ----- | -------------- |
| payout_line_items_pkey         | PK    | (id)          | —     | 主キー         |
| idx_payout_line_items_payout   | INDEX | (payout_id)   | —     | 明細一覧       |
| idx_payout_line_items_purchase | INDEX | (purchase_id) | —     | 購入から逆引き |

#### バリデーションルール

- **payout_id**: 必須、存在する creator_payouts.id を参照 / 支払い親レコード / DB（NOT NULL, FK）
- **purchase_id**: 任意、存在する purchases.id を参照 / 購入との紐付け / DB（FK）
- **amount**: 必須、0 以上の整数 / 明細金額 / DB（NOT NULL, CHECK (amount >= 0)）、アプリ（範囲チェック）

---

### user_character_relationships

#### 概要

- ユーザーとキャラクターの好感度・関係ステージ

#### カラム定義

| column           | type        | null | default           | constraints                    | description     |
| ---------------- | ----------- | ---- | ----------------- | ------------------------------ | --------------- |
| id               | uuid        | NO   | gen_random_uuid() | PK                             | 関係 ID         |
| user_id          | uuid        | NO   | —                 | FK → users(id)                 | ユーザー ID     |
| character_id     | uuid        | NO   | —                 | FK → characters(id)            | キャラクター ID |
| stage_id         | uuid        | NO   | —                 | FK → m_relationship_stages(id) | 関係ステージ ID |
| affection_points | integer     | NO   | 0                 | CHECK (affection_points >= 0)  | 好感度ポイント  |
| created_at       | timestamptz | NO   | now()             | —                              | 作成日時        |
| updated_at       | timestamptz | NO   | now()             | —                              | 更新日時        |

#### インデックス一覧

| index_name                        | type   | columns/expr            | where | purpose                |
| --------------------------------- | ------ | ----------------------- | ----- | ---------------------- |
| user_character_relationships_pkey | PK     | (id)                    | —     | 主キー                 |
| user_character_relationships_uk   | UNIQUE | (user_id, character_id) | —     | 同一組み合わせ重複防止 |
| idx_ucr_character                 | INDEX  | (character_id)          | —     | キャラクター別一覧     |
| idx_ucr_stage                     | INDEX  | (stage_id)              | —     | ステージ別一覧         |

#### バリデーションルール

- **user_id**: 必須、存在する users.id を参照 / 関係のユーザー側 / DB（NOT NULL, FK）
- **character_id**: 必須、存在する characters.id を参照 / 関係のキャラ側 / DB（NOT NULL, FK）
- **stage_id**: 必須、存在する m_relationship_stages.id を参照 / 関係ステージ / DB（NOT NULL, FK）
- **affection_points**: 必須、0 以上の整数 / 好感度ポイント / DB（NOT NULL, DEFAULT 0, CHECK）、アプリ（上限チェック・TBD）

---

### user_character_flags

#### 概要

- ユーザー × キャラ単位の状態フラグ（告白済み等）
- **updated_at を持たない**（フラグ付与/削除のみ）

#### カラム定義

| column       | type        | null | default           | constraints                        | description     |
| ------------ | ----------- | ---- | ----------------- | ---------------------------------- | --------------- |
| id           | uuid        | NO   | gen_random_uuid() | PK                                 | フラグ ID       |
| user_id      | uuid        | NO   | —                 | FK → users(id)                     | ユーザー ID     |
| character_id | uuid        | NO   | —                 | FK → characters(id)                | キャラクター ID |
| flag_code    | varchar(50) | NO   | —                 | FK → m_flag_definitions(flag_code) | フラグコード    |
| created_at   | timestamptz | NO   | now()             | —                                  | 作成日時        |

#### インデックス一覧

| index_name                | type   | columns/expr                       | where | purpose              |
| ------------------------- | ------ | ---------------------------------- | ----- | -------------------- |
| user_character_flags_pkey | PK     | (id)                               | —     | 主キー               |
| user_character_flags_uk   | UNIQUE | (user_id, character_id, flag_code) | —     | 同一フラグ重複防止   |
| idx_ucf_flag              | INDEX  | (flag_code)                        | —     | フラグ別ユーザー一覧 |

#### バリデーションルール

- **user_id**: 必須、存在する users.id を参照 / フラグのユーザー側 / DB（NOT NULL, FK）
- **character_id**: 必須、存在する characters.id を参照 / フラグのキャラ側 / DB（NOT NULL, FK）
- **flag_code**: 必須、存在する m_flag_definitions.flag_code を参照 / フラグ種別 / DB（NOT NULL, FK）

---

### user_character_memories

#### 概要

- ユーザーの呼び方、好み、NG、会話要約等

#### カラム定義

| column       | type        | null | default           | constraints         | description              |
| ------------ | ----------- | ---- | ----------------- | ------------------- | ------------------------ |
| id           | uuid        | NO   | gen_random_uuid() | PK                  | 記憶 ID                  |
| user_id      | uuid        | NO   | —                 | FK → users(id)      | ユーザー ID              |
| character_id | uuid        | NO   | —                 | FK → characters(id) | キャラクター ID          |
| nickname     | varchar(50) | YES  | —                 | —                   | ユーザーの呼び方         |
| preferences  | jsonb       | YES  | —                 | —                   | 好み・NG ワード等の JSON |
| summary      | text        | YES  | —                 | —                   | 会話要約                 |
| created_at   | timestamptz | NO   | now()             | —                   | 作成日時                 |
| updated_at   | timestamptz | NO   | now()             | —                   | 更新日時                 |

#### インデックス一覧

| index_name                   | type   | columns/expr            | where | purpose                |
| ---------------------------- | ------ | ----------------------- | ----- | ---------------------- |
| user_character_memories_pkey | PK     | (id)                    | —     | 主キー                 |
| user_character_memories_uk   | UNIQUE | (user_id, character_id) | —     | 同一組み合わせ重複防止 |

#### バリデーションルール

- **user_id**: 必須、存在する users.id を参照 / 記憶のユーザー側 / DB（NOT NULL, FK）
- **character_id**: 必須、存在する characters.id を参照 / 記憶のキャラ側 / DB（NOT NULL, FK）
- **nickname**: 任意、1-50 文字、禁止語句を含まない / ユーザーの呼び方 / アプリ（長さ、禁止語句フィルター）
- **preferences**: 任意、有効な JSON 形式 / 好み・NG ワード等 / アプリ（JSON スキーマ検証）
- **summary**: 任意、最大 10000 文字 / 会話要約 / アプリ（長さ）

---

### memory_clips

#### 概要

- ユーザーが保存した会話の切り抜き
- **updated_at を持たない**（作成のみ）

#### カラム定義

| column            | type        | null | default           | constraints                    | description     |
| ----------------- | ----------- | ---- | ----------------- | ------------------------------ | --------------- |
| id                | uuid        | NO   | gen_random_uuid() | PK                             | クリップ ID     |
| user_id           | uuid        | NO   | —                 | FK → users(id)                 | ユーザー ID     |
| character_id      | uuid        | NO   | —                 | FK → characters(id)            | キャラクター ID |
| source_message_id | uuid        | YES  | —                 | FK → conversation_messages(id) | 元メッセージ ID |
| content           | text        | YES  | —                 | —                              | クリップ内容    |
| created_at        | timestamptz | NO   | now()             | —                              | 作成日時        |

#### インデックス一覧

| index_name                         | type  | columns/expr                             | where | purpose                |
| ---------------------------------- | ----- | ---------------------------------------- | ----- | ---------------------- |
| memory_clips_pkey                  | PK    | (id)                                     | —     | 主キー                 |
| idx_memory_clips_user_char_created | INDEX | (user_id, character_id, created_at DESC) | —     | メモリー一覧（新着順） |
| idx_memory_clips_message           | INDEX | (source_message_id)                      | —     | 元メッセージ逆引き     |

#### バリデーションルール

- **user_id**: 必須、存在する users.id を参照 / クリップ所有者 / DB（NOT NULL, FK）
- **character_id**: 必須、存在する characters.id を参照 / クリップ対象キャラ / DB（NOT NULL, FK）
- **source_message_id**: 任意、存在する conversation_messages.id を参照 / 元メッセージ / DB（FK）
- **content**: 任意、最大 5000 文字 / クリップ内容 / アプリ（長さ）

---

### voice_packs

#### 概要

- 音声素材のセット（メタ情報）

#### カラム定義

| column       | type         | null | default           | constraints             | description                       |
| ------------ | ------------ | ---- | ----------------- | ----------------------- | --------------------------------- |
| id           | uuid         | NO   | gen_random_uuid() | PK                      | ボイスパック ID                   |
| character_id | uuid         | NO   | —                 | FK → characters(id)     | キャラクター ID                   |
| name         | varchar(100) | YES  | —                 | —                       | パック名                          |
| status       | smallint     | NO   | 1                 | CHECK (status IN (1,2)) | ステータス（1:draft/2:published） |
| created_at   | timestamptz  | NO   | now()             | —                       | 作成日時                          |
| updated_at   | timestamptz  | NO   | now()             | —                       | 更新日時                          |
| deleted_at   | timestamptz  | YES  | —                 | —                       | 論理削除日時                      |

#### インデックス一覧

| index_name                       | type  | columns/expr   | where              | purpose            |
| -------------------------------- | ----- | -------------- | ------------------ | ------------------ |
| voice_packs_pkey                 | PK    | (id)           | —                  | 主キー             |
| idx_voice_packs_character_active | INDEX | (character_id) | deleted_at IS NULL | キャラクター別一覧 |

#### バリデーションルール

- **character_id**: 必須、存在する characters.id を参照 / 所属キャラクター / DB（NOT NULL, FK）
- **name**: 任意、1-100 文字 / パック名 / アプリ（長さ）
- **status**: 必須、1/2 のいずれか / 公開状態 / DB（NOT NULL, DEFAULT 1, CHECK）、アプリ（enum 値チェック）

---

### voice_assets

#### 概要

- 個別の音声ファイル実体

#### カラム定義

| column            | type         | null | default           | constraints                 | description      |
| ----------------- | ------------ | ---- | ----------------- | --------------------------- | ---------------- |
| id                | uuid         | NO   | gen_random_uuid() | PK                          | 音声アセット ID  |
| voice_pack_id     | uuid         | NO   | —                 | FK → voice_packs(id)        | ボイスパック ID  |
| voice_category_id | uuid         | NO   | —                 | FK → m_voice_categories(id) | 音声カテゴリ ID  |
| file_url          | varchar(500) | NO   | —                 | —                           | ファイル URL     |
| duration_ms       | integer      | YES  | —                 | —                           | 音声長（ミリ秒） |
| transcript        | text         | YES  | —                 | —                           | 書き起こし       |
| created_at        | timestamptz  | NO   | now()             | —                           | 作成日時         |
| updated_at        | timestamptz  | NO   | now()             | —                           | 更新日時         |

#### インデックス一覧

| index_name                | type  | columns/expr        | where | purpose        |
| ------------------------- | ----- | ------------------- | ----- | -------------- |
| voice_assets_pkey         | PK    | (id)                | —     | 主キー         |
| idx_voice_assets_pack     | INDEX | (voice_pack_id)     | —     | パック内一覧   |
| idx_voice_assets_category | INDEX | (voice_category_id) | —     | カテゴリ別一覧 |

#### バリデーションルール

- **voice_pack_id**: 必須、存在する voice_packs.id を参照 / 所属パック / DB（NOT NULL, FK）
- **voice_category_id**: 必須、存在する m_voice_categories.id を参照 / 音声カテゴリ / DB（NOT NULL, FK）
- **file_url**: 必須、1-500 文字、https のみ、許可ドメイン、IP 直指定禁止 / ファイル URL / DB（NOT NULL）、アプリ（URL 共通ルール）
- **duration_ms**: 任意、0 以上の整数 / 音声長 / アプリ（範囲チェック）
- **transcript**: 任意、最大 2000 文字 / 書き起こし / アプリ（長さ）

---

### rights_consents

#### 概要

- 音声アップロード時の権利同意・宣誓記録
- **updated_at を持たない**（同意記録のみ）

#### カラム定義

| column            | type         | null | default           | constraints               | description            |
| ----------------- | ------------ | ---- | ----------------- | ------------------------- | ---------------------- |
| id                | uuid         | NO   | gen_random_uuid() | PK                        | 権利同意 ID            |
| voice_asset_id    | uuid         | NO   | —                 | FK → voice_assets(id), UK | 音声アセット ID（1:1） |
| consenter_name    | varchar(100) | NO   | —                 | —                         | 同意者氏名             |
| consenter_contact | varchar(255) | NO   | —                 | —                         | 同意者連絡先           |
| consent_statement | text         | NO   | —                 | —                         | 同意宣誓内容           |
| consented_at      | timestamptz  | NO   | now()             | —                         | 同意日時               |
| created_at        | timestamptz  | NO   | now()             | —                         | 作成日時               |

#### インデックス一覧

| index_name                         | type   | columns/expr     | where | purpose      |
| ---------------------------------- | ------ | ---------------- | ----- | ------------ |
| rights_consents_pkey               | PK     | (id)             | —     | 主キー       |
| rights_consents_voice_asset_id_key | UNIQUE | (voice_asset_id) | —     | 1:1 関係担保 |

#### バリデーションルール

- **voice_asset_id**: 必須、存在する voice_assets.id を参照、一意 / 1 アセット=1 同意 / DB（NOT NULL, FK, UK）
- **consenter_name**: 必須、1-100 文字 / 同意者氏名 / DB（NOT NULL）、アプリ（長さ）
- **consenter_contact**: 必須、1-255 文字、メールまたは電話番号形式 / 同意者連絡先 / DB（NOT NULL）、アプリ（形式チェック）
- **consent_statement**: 必須、最大 5000 文字、所定の宣誓文を含む / 同意宣誓内容 / DB（NOT NULL）、アプリ（必須文言チェック）
- **consented_at**: 必須、過去〜現在の日時 / 同意日時 / DB（NOT NULL, DEFAULT now()）

---

### events

#### 概要

- キャラクターに紐づく特別イベントの定義（告白、記念日等）

#### カラム定義

| column        | type         | null | default           | constraints             | description                       |
| ------------- | ------------ | ---- | ----------------- | ----------------------- | --------------------------------- |
| id            | uuid         | NO   | gen_random_uuid() | PK                      | イベント ID                       |
| character_id  | uuid         | NO   | —                 | FK → characters(id)     | キャラクター ID                   |
| event_type_id | uuid         | YES  | —                 | FK → m_event_types(id)  | イベント種別 ID（暫定 NULL 可）   |
| name          | varchar(100) | NO   | —                 | —                       | イベント名                        |
| description   | text         | YES  | —                 | —                       | 説明文                            |
| status        | smallint     | NO   | 1                 | CHECK (status IN (1,2)) | ステータス（1:draft/2:published） |
| created_at    | timestamptz  | NO   | now()             | —                       | 作成日時                          |
| updated_at    | timestamptz  | NO   | now()             | —                       | 更新日時                          |
| deleted_at    | timestamptz  | YES  | —                 | —                       | 論理削除日時                      |

#### インデックス一覧

| index_name                         | type  | columns/expr           | where              | purpose                    |
| ---------------------------------- | ----- | ---------------------- | ------------------ | -------------------------- |
| events_pkey                        | PK    | (id)                   | —                  | 主キー                     |
| idx_events_character_status_active | INDEX | (character_id, status) | deleted_at IS NULL | キャラクター別イベント一覧 |
| idx_events_type                    | INDEX | (event_type_id)        | —                  | イベント種別別一覧         |

#### バリデーションルール

- **character_id**: 必須、存在する characters.id を参照 / 所属キャラクター / DB（NOT NULL, FK）
- **event_type_id**: 任意、存在する m_event_types.id を参照 / イベント種別（暫定 NULL 可） / DB（FK）
- **name**: 必須、1-100 文字、禁止語句を含まない / イベント名 / DB（NOT NULL）、アプリ（長さ、禁止語句フィルター）
- **description**: 任意、最大 5000 文字、禁止語句を含まない / 説明文 / アプリ（長さ、禁止語句フィルター）
- **status**: 必須、1/2 のいずれか / 公開状態 / DB（NOT NULL, DEFAULT 1, CHECK）、アプリ（enum 値チェック）

---

### event_unlock_conditions

#### 概要

- イベント解放に必要な条件

#### カラム定義

| column                | type        | null | default           | constraints                                                      | description     |
| --------------------- | ----------- | ---- | ----------------- | ---------------------------------------------------------------- | --------------- |
| id                    | uuid        | NO   | gen_random_uuid() | PK                                                               | 解放条件 ID     |
| event_id              | uuid        | NO   | —                 | FK → events(id)                                                  | イベント ID     |
| condition_type        | varchar(20) | NO   | —                 | CHECK (condition_type IN ('flag','affection','event_completed')) | 条件種別        |
| prerequisite_event_id | uuid        | YES  | —                 | FK → events(id)                                                  | 前提イベント ID |
| flag_code             | varchar(50) | YES  | —                 | FK → m_flag_definitions(flag_code)                               | フラグコード    |
| affection_threshold   | integer     | YES  | —                 | —                                                                | 好感度閾値      |
| created_at            | timestamptz | NO   | now()             | —                                                                | 作成日時        |
| updated_at            | timestamptz | NO   | now()             | —                                                                | 更新日時        |

#### インデックス一覧

| index_name                   | type  | columns/expr            | where | purpose            |
| ---------------------------- | ----- | ----------------------- | ----- | ------------------ |
| event_unlock_conditions_pkey | PK    | (id)                    | —     | 主キー             |
| idx_euc_event                | INDEX | (event_id)              | —     | イベント別条件一覧 |
| idx_euc_prerequisite         | INDEX | (prerequisite_event_id) | —     | 前提イベント逆引き |
| idx_euc_flag                 | INDEX | (flag_code)             | —     | フラグ別条件       |
| idx_euc_condition_type       | INDEX | (condition_type)        | —     | 条件種別別         |

#### バリデーションルール

- **event_id**: 必須、存在する events.id を参照 / 対象イベント / DB（NOT NULL, FK）
- **condition_type**: 必須、許可値：flag/affection/event_completed / 条件種別 / DB（NOT NULL, CHECK）、アプリ（enum 値チェック）
- **prerequisite_event_id**: condition_type='event_completed'時は必須、存在する events.id を参照 / 前提イベント / DB（FK）、アプリ（排他チェック）
- **flag_code**: condition_type='flag'時は必須、存在する m_flag_definitions.flag_code を参照 / 対象フラグ / DB（FK）、アプリ（排他チェック）
- **affection_threshold**: condition_type='affection'時は必須、0 以上の整数 / 好感度閾値 / アプリ（排他チェック、範囲チェック）

---

### event_script_nodes

#### 概要

- イベント台本のセリフ・選択肢・分岐定義

#### カラム定義

| column         | type        | null | default           | constraints           | description     |
| -------------- | ----------- | ---- | ----------------- | --------------------- | --------------- |
| id             | uuid        | NO   | gen_random_uuid() | PK                    | ノード ID       |
| event_id       | uuid        | NO   | —                 | FK → events(id)       | イベント ID     |
| node_type      | varchar(20) | NO   | —                 | —                     | ノード種別      |
| content        | text        | YES  | —                 | —                     | セリフ内容      |
| voice_asset_id | uuid        | YES  | —                 | FK → voice_assets(id) | 音声アセット ID |
| sort_order     | smallint    | NO   | 0                 | —                     | 表示順          |
| created_at     | timestamptz | NO   | now()             | —                     | 作成日時        |
| updated_at     | timestamptz | NO   | now()             | —                     | 更新日時        |

#### インデックス一覧

| index_name              | type  | columns/expr           | where | purpose            |
| ----------------------- | ----- | ---------------------- | ----- | ------------------ |
| event_script_nodes_pkey | PK    | (id)                   | —     | 主キー             |
| idx_esn_event_sort      | INDEX | (event_id, sort_order) | —     | 台本ノード順序取得 |
| idx_esn_voice_asset     | INDEX | (voice_asset_id)       | —     | 音声アセット逆引き |

#### バリデーションルール

- **event_id**: 必須、存在する events.id を参照 / 所属イベント / DB（NOT NULL, FK）
- **node_type**: 必須、1-20 文字、許可値：line/choice/action 等 / ノード種別 / DB（NOT NULL）、アプリ（enum 値チェック）
- **content**: 任意、最大 5000 文字、変数プレースホルダーは有効な形式 / セリフ内容 / アプリ（長さ、プレースホルダー形式チェック）
- **voice_asset_id**: 任意、存在する voice_assets.id を参照 / 音声アセット / DB（FK）
- **sort_order**: 必須、0 以上の整数 / 表示順序 / DB（NOT NULL, DEFAULT 0）、アプリ（範囲チェック）

---

### event_branch_options

#### 概要

- 分岐ノードの選択肢と遷移先

#### カラム定義

| column       | type         | null | default           | constraints                 | description     |
| ------------ | ------------ | ---- | ----------------- | --------------------------- | --------------- |
| id           | uuid         | NO   | gen_random_uuid() | PK                          | 選択肢 ID       |
| node_id      | uuid         | NO   | —                 | FK → event_script_nodes(id) | ノード ID       |
| option_text  | varchar(200) | NO   | —                 | —                           | 選択肢テキスト  |
| next_node_id | uuid         | YES  | —                 | FK → event_script_nodes(id) | 遷移先ノード ID |
| sort_order   | smallint     | NO   | 0                 | —                           | 表示順          |
| created_at   | timestamptz  | NO   | now()             | —                           | 作成日時        |
| updated_at   | timestamptz  | NO   | now()             | —                           | 更新日時        |

#### インデックス一覧

| index_name                | type  | columns/expr          | where | purpose            |
| ------------------------- | ----- | --------------------- | ----- | ------------------ |
| event_branch_options_pkey | PK    | (id)                  | —     | 主キー             |
| idx_ebo_node_sort         | INDEX | (node_id, sort_order) | —     | 分岐選択肢順序取得 |
| idx_ebo_next_node         | INDEX | (next_node_id)        | —     | 遷移先ノード逆引き |

#### バリデーションルール

- **node_id**: 必須、存在する event_script_nodes.id を参照 / 所属ノード / DB（NOT NULL, FK）
- **option_text**: 必須、1-200 文字 / 選択肢テキスト / DB（NOT NULL）、アプリ（長さ）
- **next_node_id**: 任意、存在する event_script_nodes.id を参照、同一イベント内 / 遷移先ノード / DB（FK）、アプリ（同一イベントチェック）
- **sort_order**: 必須、0 以上の整数 / 表示順序 / DB（NOT NULL, DEFAULT 0）、アプリ（範囲チェック）

---

### user_event_completions

#### 概要

- ユーザーがクリアしたイベントの記録
- **updated_at を持たない**（クリア記録のみ）

#### カラム定義

| column       | type        | null | default           | constraints     | description   |
| ------------ | ----------- | ---- | ----------------- | --------------- | ------------- |
| id           | uuid        | NO   | gen_random_uuid() | PK              | クリア履歴 ID |
| user_id      | uuid        | NO   | —                 | FK → users(id)  | ユーザー ID   |
| event_id     | uuid        | NO   | —                 | FK → events(id) | イベント ID   |
| completed_at | timestamptz | NO   | now()             | —               | クリア日時    |
| created_at   | timestamptz | NO   | now()             | —               | 作成日時      |

#### インデックス一覧

| index_name                  | type   | columns/expr                 | where | purpose              |
| --------------------------- | ------ | ---------------------------- | ----- | -------------------- |
| user_event_completions_pkey | PK     | (id)                         | —     | 主キー               |
| user_event_completions_uk   | UNIQUE | (user_id, event_id)          | —     | 重複クリア記録防止   |
| idx_uec_user_completed      | INDEX  | (user_id, completed_at DESC) | —     | クリア履歴（新着順） |
| idx_uec_event               | INDEX  | (event_id)                   | —     | クリアユーザー数集計 |

#### バリデーションルール

- **user_id**: 必須、存在する users.id を参照 / クリアユーザー / DB（NOT NULL, FK）
- **event_id**: 必須、存在する events.id を参照 / クリアイベント / DB（NOT NULL, FK）
- **completed_at**: 必須、過去〜現在の日時 / クリア日時 / DB（NOT NULL, DEFAULT now()）

---

### conversation_sessions

#### 概要

- ユーザーとキャラクターの会話単位

#### カラム定義

| column       | type        | null | default           | constraints                              | description     |
| ------------ | ----------- | ---- | ----------------- | ---------------------------------------- | --------------- |
| id           | uuid        | NO   | gen_random_uuid() | PK                                       | セッション ID   |
| user_id      | uuid        | NO   | —                 | FK → users(id)                           | ユーザー ID     |
| character_id | uuid        | NO   | —                 | FK → characters(id)                      | キャラクター ID |
| session_type | varchar(20) | NO   | 'free'            | CHECK (session_type IN ('free','event')) | セッション種別  |
| event_id     | uuid        | YES  | —                 | FK → events(id)                          | イベント ID     |
| started_at   | timestamptz | NO   | now()             | —                                        | 開始日時        |
| ended_at     | timestamptz | YES  | —                 | —                                        | 終了日時        |
| created_at   | timestamptz | NO   | now()             | —                                        | 作成日時        |
| updated_at   | timestamptz | NO   | now()             | —                                        | 更新日時        |

#### インデックス一覧

| index_name                 | type  | columns/expr                             | where | purpose                         |
| -------------------------- | ----- | ---------------------------------------- | ----- | ------------------------------- |
| conversation_sessions_pkey | PK    | (id)                                     | —     | 主キー                          |
| idx_cs_user_char_started   | INDEX | (user_id, character_id, started_at DESC) | —     | ユーザー × キャラクター会話履歴 |
| idx_cs_user_started        | INDEX | (user_id, started_at DESC)               | —     | ユーザー全会話一覧              |
| idx_cs_character           | INDEX | (character_id)                           | —     | キャラクター別会話統計          |
| idx_cs_event               | INDEX | (event_id)                               | —     | イベント会話取得                |
| idx_cs_session_type        | INDEX | (session_type)                           | —     | セッション種別別                |

#### バリデーションルール

- **user_id**: 必須、存在する users.id を参照 / 会話ユーザー / DB（NOT NULL, FK）
- **character_id**: 必須、存在する characters.id を参照 / 会話キャラクター / DB（NOT NULL, FK）
- **session_type**: 必須、許可値：free/event / セッション種別 / DB（NOT NULL, DEFAULT 'free', CHECK）、アプリ（enum 値チェック）
- **event_id**: session_type='event'時は必須、存在する events.id を参照 / イベント ID / DB（FK）、アプリ（session_type との整合性チェック）
- **started_at**: 必須、過去〜現在の日時 / 開始日時 / DB（NOT NULL, DEFAULT now()）
- **ended_at**: 任意、started_at 以後の日時 / 終了日時 / アプリ（範囲チェック）

---

### conversation_messages

#### 概要

- 会話内の個別発話・応答ログ
- **deleted_at を持たない例外テーブル**（証跡として永続保存）
- **updated_at を持たない**（メッセージログは更新しない）

#### カラム定義

| column     | type        | null | default           | constraints                          | description    |
| ---------- | ----------- | ---- | ----------------- | ------------------------------------ | -------------- |
| id         | uuid        | NO   | gen_random_uuid() | PK                                   | メッセージ ID  |
| session_id | uuid        | NO   | —                 | FK → conversation_sessions(id)       | セッション ID  |
| role       | varchar(20) | NO   | —                 | CHECK (role IN ('user','character')) | 発話者役割     |
| content    | text        | NO   | —                 | —                                    | メッセージ内容 |
| created_at | timestamptz | NO   | now()             | —                                    | 作成日時       |

#### インデックス一覧

| index_name                 | type  | columns/expr                 | where | purpose                          |
| -------------------------- | ----- | ---------------------------- | ----- | -------------------------------- |
| conversation_messages_pkey | PK    | (id)                         | —     | 主キー                           |
| idx_cm_session_created     | INDEX | (session_id, created_at ASC) | —     | セッション内メッセージ時系列取得 |

#### バリデーションルール

- **session_id**: 必須、存在する conversation_sessions.id を参照 / 所属セッション / DB（NOT NULL, FK）
- **role**: 必須、許可値：user/character / 発話者役割 / DB（NOT NULL, CHECK）、アプリ（enum 値チェック）
- **content**: 必須、1-10000 文字、有害コンテンツフィルター / メッセージ内容 / DB（NOT NULL）、アプリ（長さ、コンテンツフィルター）

---

### reports

#### 概要

- ユーザーからの通報内容
- ポリモーフィック参照（target_type + target_id）

#### カラム定義

| column           | type        | null | default           | constraints                                                           | description                                              |
| ---------------- | ----------- | ---- | ----------------- | --------------------------------------------------------------------- | -------------------------------------------------------- |
| id               | uuid        | NO   | gen_random_uuid() | PK                                                                    | 通報 ID                                                  |
| reporter_user_id | uuid        | YES  | —                 | FK → users(id)                                                        | 通報者 ID（退会時は参照維持/匿名化で対応）               |
| reason_id        | uuid        | NO   | —                 | FK → m_report_reasons(id)                                             | 通報理由 ID                                              |
| target_type      | varchar(30) | NO   | —                 | CHECK (target_type IN ('character','conversation_message','creator')) | 対象種別                                                 |
| target_id        | uuid        | NO   | —                 | —                                                                     | 対象 ID（ポリモーフィック）                              |
| detail           | text        | YES  | —                 | —                                                                     | 詳細コメント                                             |
| status           | smallint    | NO   | 1                 | CHECK (status IN (1,2,3,4))                                           | ステータス（1:open/2:in_progress/3:resolved/4:rejected） |
| created_at       | timestamptz | NO   | now()             | —                                                                     | 作成日時                                                 |
| updated_at       | timestamptz | NO   | now()             | —                                                                     | 更新日時                                                 |

#### インデックス一覧

| index_name                 | type  | columns/expr              | where | purpose                |
| -------------------------- | ----- | ------------------------- | ----- | ---------------------- |
| reports_pkey               | PK    | (id)                      | —     | 主キー                 |
| idx_reports_reporter       | INDEX | (reporter_user_id)        | —     | 通報者別一覧           |
| idx_reports_reason         | INDEX | (reason_id)               | —     | 理由別一覧             |
| idx_reports_target         | INDEX | (target_type, target_id)  | —     | ポリモーフィック対象別 |
| idx_reports_status_created | INDEX | (status, created_at DESC) | —     | ステータス別一覧       |

#### バリデーションルール

- **reporter_user_id**: 任意、存在する users.id を参照 / 通報者（退会時の扱いはアプリ層で対応：参照維持または匿名化） / DB（FK）
- **reason_id**: 必須、存在する m_report_reasons.id を参照 / 通報理由 / DB（NOT NULL, FK）
- **target_type**: 必須、許可値：character/conversation_message/creator / 対象種別 / DB（NOT NULL, CHECK）、アプリ（enum 値チェック）
- **target_id**: 必須、UUID 形式、target_type に応じた存在チェック必須 / ポリモーフィック対象 ID / アプリ（存在チェック必須）
- **detail**: 任意、最大 2000 文字 / 詳細コメント / アプリ（長さ）
- **status**: 必須、1/2/3/4 のいずれか / 対応状態 / DB（NOT NULL, DEFAULT 1, CHECK）、アプリ（enum 値チェック）

**ポリモーフィック参照先**:
| target_type | 参照先テーブル | 存在チェック条件 |
|-------------|---------------|-----------------|
| character | characters | `id = :target_id AND deleted_at IS NULL` |
| conversation_message | conversation_messages | `id = :target_id`（deleted_at なし） |
| creator | creators | `id = :target_id AND deleted_at IS NULL` |

---

### moderation_actions

#### 概要

- 運営による対応記録（公開停止等）

#### カラム定義

| column        | type        | null | default           | constraints                                               | description                        |
| ------------- | ----------- | ---- | ----------------- | --------------------------------------------------------- | ---------------------------------- |
| id            | uuid        | NO   | gen_random_uuid() | PK                                                        | 対応 ID                            |
| report_id     | uuid        | YES  | —                 | FK → reports(id)                                          | 通報 ID（通報起因でない場合 NULL） |
| admin_user_id | uuid        | NO   | —                 | FK → admin_users(id)                                      | 対応者 ID                          |
| action_type   | varchar(20) | NO   | —                 | CHECK (action_type IN ('suspend','restore','warn','ban')) | 対応種別                           |
| target_type   | varchar(30) | YES  | —                 | —                                                         | 対象種別                           |
| target_id     | uuid        | YES  | —                 | —                                                         | 対象 ID                            |
| reason        | text        | YES  | —                 | —                                                         | 対応理由                           |
| created_at    | timestamptz | NO   | now()             | —                                                         | 作成日時                           |

#### インデックス一覧

| index_name                 | type  | columns/expr                     | where | purpose                |
| -------------------------- | ----- | -------------------------------- | ----- | ---------------------- |
| moderation_actions_pkey    | PK    | (id)                             | —     | 主キー                 |
| idx_ma_report              | INDEX | (report_id)                      | —     | 通報から対応履歴取得   |
| idx_ma_admin_created       | INDEX | (admin_user_id, created_at DESC) | —     | 運営ユーザー別対応履歴 |
| idx_ma_action_type_created | INDEX | (action_type, created_at DESC)   | —     | 対応種別別履歴         |

#### バリデーションルール

- **report_id**: 任意、存在する reports.id を参照 / 関連通報 / DB（FK）
- **admin_user_id**: 必須、存在する admin_users.id を参照 / 対応者 / DB（NOT NULL, FK）
- **action_type**: 必須、許可値：suspend/restore/warn/ban / 対応種別 / DB（NOT NULL, CHECK）、アプリ（enum 値チェック）
- **target_type**: 任意、許可値：character/creator/user 等 / 対象種別 / アプリ（enum 値チェック）
- **target_id**: 任意、UUID 形式、target_type に応じた存在チェック / 対象 ID / アプリ（存在チェック）
- **reason**: 任意、最大 2000 文字 / 対応理由 / アプリ（長さ）

---

### appeals

#### 概要

- クリエイターからの異議申し立て

#### カラム定義

| column               | type        | null | default           | constraints                     | description                                   |
| -------------------- | ----------- | ---- | ----------------- | ------------------------------- | --------------------------------------------- |
| id                   | uuid        | NO   | gen_random_uuid() | PK                              | 異議申し立て ID                               |
| moderation_action_id | uuid        | NO   | —                 | FK → moderation_actions(id), UK | モデレーション対応 ID（0..1 関係）            |
| appeal_text          | text        | NO   | —                 | —                               | 申し立て内容                                  |
| status               | smallint    | NO   | 1                 | CHECK (status IN (1,2,3))       | ステータス（1:pending/2:approved/3:rejected） |
| created_at           | timestamptz | NO   | now()             | —                               | 作成日時                                      |
| updated_at           | timestamptz | NO   | now()             | —                               | 更新日時                                      |

#### インデックス一覧

| index_name                       | type   | columns/expr           | where | purpose          |
| -------------------------------- | ------ | ---------------------- | ----- | ---------------- |
| appeals_pkey                     | PK     | (id)                   | —     | 主キー           |
| appeals_moderation_action_id_key | UNIQUE | (moderation_action_id) | —     | 0..1 関係担保    |
| idx_appeals_status               | INDEX  | (status)               | —     | ステータス別一覧 |

#### バリデーションルール

- **moderation_action_id**: 必須、存在する moderation_actions.id を参照、一意 / 対象アクション / DB（NOT NULL, FK, UK）
- **appeal_text**: 必須、1-5000 文字 / 申し立て内容 / DB（NOT NULL）、アプリ（長さ）
- **status**: 必須、1/2/3 のいずれか / 申し立て状態 / DB（NOT NULL, DEFAULT 1, CHECK）、アプリ（enum 値チェック）

---

### user_blocks

#### 概要

- ユーザーによるブロック設定
- ポリモーフィック参照（target_type + target_id）

#### カラム定義

| column      | type        | null | default           | constraints                                           | description                   |
| ----------- | ----------- | ---- | ----------------- | ----------------------------------------------------- | ----------------------------- |
| id          | uuid        | NO   | gen_random_uuid() | PK                                                    | ブロック ID                   |
| user_id     | uuid        | NO   | —                 | FK → users(id)                                        | ユーザー ID                   |
| target_type | varchar(30) | NO   | —                 | CHECK (target_type IN ('user','creator','character')) | 対象種別                      |
| target_id   | uuid        | NO   | —                 | —                                                     | 対象 ID（ポリモーフィック）   |
| created_at  | timestamptz | NO   | now()             | —                                                     | 作成日時                      |
| deleted_at  | timestamptz | YES  | —                 | —                                                     | 論理削除日時（=ブロック解除） |

#### インデックス一覧

| index_name                          | type         | columns/expr                      | where              | purpose                    |
| ----------------------------------- | ------------ | --------------------------------- | ------------------ | -------------------------- |
| user_blocks_pkey                    | PK           | (id)                              | —                  | 主キー                     |
| user_blocks_active_uk               | UNIQUE INDEX | (user_id, target_type, target_id) | deleted_at IS NULL | アクティブブロック重複防止 |
| idx_user_blocks_user_created_active | INDEX        | (user_id, created_at DESC)        | deleted_at IS NULL | ブロック一覧（新着順）     |
| idx_user_blocks_target_active       | INDEX        | (target_type, target_id)          | deleted_at IS NULL | ポリモーフィック逆引き     |

```sql
CREATE UNIQUE INDEX user_blocks_active_uk
  ON user_blocks (user_id, target_type, target_id)
  WHERE deleted_at IS NULL;
```

#### バリデーションルール

- **user_id**: 必須、存在する users.id を参照 / ブロック実行者 / DB（NOT NULL, FK）
- **target_type**: 必須、許可値：user/creator/character / 対象種別 / DB（NOT NULL, CHECK）、アプリ（enum 値チェック）
- **target_id**: 必須、UUID 形式、target_type に応じた存在チェック必須かつ deleted_at IS NULL であること / ポリモーフィック対象 ID / アプリ（存在チェック＋論理削除チェック必須）
- **ビジネスルール**: 自分自身のブロック禁止 → アプリ側でチェック

**ポリモーフィック参照先**:
| target_type | 参照先テーブル | 存在チェック条件 |
|-------------|---------------|-----------------|
| user | users | `id = :target_id AND deleted_at IS NULL` |
| creator | creators | `id = :target_id AND deleted_at IS NULL` |
| character | characters | `id = :target_id AND deleted_at IS NULL` |

---

### terms_agreements

#### 概要

- ユーザー/クリエイター/運営の規約同意記録
- ポリモーフィック参照（actor_type + actor_id）
- **updated_at を持たない**（同意記録のみ）

#### カラム定義

| column        | type        | null | default           | constraints                                           | description                   |
| ------------- | ----------- | ---- | ----------------- | ----------------------------------------------------- | ----------------------------- |
| id            | uuid        | NO   | gen_random_uuid() | PK                                                    | 同意 ID                       |
| actor_type    | varchar(30) | NO   | —                 | CHECK (actor_type IN ('user','creator','admin_user')) | 同意者種別                    |
| actor_id      | uuid        | NO   | —                 | —                                                     | 同意者 ID（ポリモーフィック） |
| terms_type    | varchar(30) | NO   | —                 | CHECK (terms_type IN ('tos','privacy'))               | 規約種別                      |
| terms_version | varchar(20) | NO   | —                 | —                                                     | 規約バージョン                |
| agreed_at     | timestamptz | NO   | now()             | —                                                     | 同意日時                      |
| created_at    | timestamptz | NO   | now()             | —                                                     | 作成日時                      |

#### インデックス一覧

| index_name            | type   | columns/expr                                      | where | purpose                    |
| --------------------- | ------ | ------------------------------------------------- | ----- | -------------------------- |
| terms_agreements_pkey | PK     | (id)                                              | —     | 主キー                     |
| terms_agreements_uk   | UNIQUE | (actor_type, actor_id, terms_type, terms_version) | —     | 同一バージョン重複同意防止 |
| idx_ta_terms          | INDEX  | (terms_type, terms_version)                       | —     | 規約バージョン別同意者数   |

#### バリデーションルール

- **actor_type**: 必須、許可値：user/creator/admin_user / 同意者種別 / DB（NOT NULL, CHECK）、アプリ（enum 値チェック）
- **actor_id**: 必須、UUID 形式、actor_type に応じた存在チェック必須かつ deleted_at IS NULL であること / ポリモーフィック同意者 ID / アプリ（存在チェック＋論理削除チェック必須）
- **terms_type**: 必須、許可値：tos/privacy / 規約種別 / DB（NOT NULL, CHECK）、アプリ（enum 値チェック）
- **terms_version**: 必須、1-20 文字、セマンティックバージョン形式推奨 / 規約バージョン / DB（NOT NULL）、アプリ（形式チェック）
- **agreed_at**: 必須、過去〜現在の日時 / 同意日時 / DB（NOT NULL, DEFAULT now()）

**ポリモーフィック参照先**:
| actor_type | 参照先テーブル | 存在チェック条件 |
|------------|---------------|-----------------|
| user | users | `id = :actor_id AND deleted_at IS NULL` |
| creator | creators | `id = :actor_id AND deleted_at IS NULL` |
| admin_user | admin_users | `id = :actor_id AND deleted_at IS NULL` |

---

### data_deletion_requests

#### 概要

- ユーザーからのデータ削除要求とその対応状況

#### カラム定義

| column       | type        | null | default           | constraints                 | description                                                   |
| ------------ | ----------- | ---- | ----------------- | --------------------------- | ------------------------------------------------------------- |
| id           | uuid        | NO   | gen_random_uuid() | PK                          | 削除要求 ID                                                   |
| user_id      | uuid        | NO   | —                 | FK → users(id)              | ユーザー ID                                                   |
| status       | smallint    | NO   | 1                 | CHECK (status IN (1,2,3,4)) | ステータス（1:requested/2:processing/3:completed/4:rejected） |
| requested_at | timestamptz | NO   | now()             | —                           | 要求日時                                                      |
| completed_at | timestamptz | YES  | —                 | —                           | 完了日時                                                      |
| created_at   | timestamptz | NO   | now()             | —                           | 作成日時                                                      |
| updated_at   | timestamptz | NO   | now()             | —                           | 更新日時                                                      |

#### インデックス一覧

| index_name                  | type  | columns/expr               | where | purpose                    |
| --------------------------- | ----- | -------------------------- | ----- | -------------------------- |
| data_deletion_requests_pkey | PK    | (id)                       | —     | 主キー                     |
| idx_ddr_user                | INDEX | (user_id)                  | —     | ユーザー別要求履歴         |
| idx_ddr_status_requested    | INDEX | (status, requested_at ASC) | —     | ステータス別一覧（古い順） |

#### バリデーションルール

- **user_id**: 必須、存在する users.id を参照 / 要求者 / DB（NOT NULL, FK）
- **status**: 必須、1/2/3/4 のいずれか / 要求状態 / DB（NOT NULL, DEFAULT 1, CHECK）、アプリ（enum 値チェック）
- **requested_at**: 必須、過去〜現在の日時 / 要求日時 / DB（NOT NULL, DEFAULT now()）
- **completed_at**: 任意、requested_at 以後の日時 / 完了日時 / アプリ（範囲チェック、完了時に自動セット）

---

### data_export_requests

#### 概要

- ユーザーからのデータエクスポート要求

#### カラム定義

| column       | type         | null | default           | constraints                 | description                                              |
| ------------ | ------------ | ---- | ----------------- | --------------------------- | -------------------------------------------------------- |
| id           | uuid         | NO   | gen_random_uuid() | PK                          | エクスポート要求 ID                                      |
| user_id      | uuid         | NO   | —                 | FK → users(id)              | ユーザー ID                                              |
| status       | smallint     | NO   | 1                 | CHECK (status IN (1,2,3,4)) | ステータス（1:requested/2:processing/3:ready/4:expired） |
| file_url     | varchar(500) | YES  | —                 | —                           | ダウンロード URL                                         |
| expires_at   | timestamptz  | YES  | —                 | —                           | 有効期限                                                 |
| requested_at | timestamptz  | NO   | now()             | —                           | 要求日時                                                 |
| created_at   | timestamptz  | NO   | now()             | —                           | 作成日時                                                 |
| updated_at   | timestamptz  | NO   | now()             | —                           | 更新日時                                                 |

#### インデックス一覧

| index_name                | type  | columns/expr               | where | purpose                    |
| ------------------------- | ----- | -------------------------- | ----- | -------------------------- |
| data_export_requests_pkey | PK    | (id)                       | —     | 主キー                     |
| idx_der_user              | INDEX | (user_id)                  | —     | ユーザー別要求履歴         |
| idx_der_status_requested  | INDEX | (status, requested_at ASC) | —     | ステータス別一覧（古い順） |

#### バリデーションルール

- **user_id**: 必須、存在する users.id を参照 / 要求者 / DB（NOT NULL, FK）
- **status**: 必須、1/2/3/4 のいずれか / 要求状態 / DB（NOT NULL, DEFAULT 1, CHECK）、アプリ（enum 値チェック）
- **file_url**: status=3(ready)時は必須、最大 500 文字、https のみ、許可ドメイン、IP 直指定禁止、署名付き URL 推奨 / ダウンロード URL / アプリ（条件付き必須、URL 共通ルール）
- **expires_at**: status IN (3,4)時は必須、status=3 なら未来、status=4 なら過去〜現在 / 有効期限 / アプリ（条件付き必須、範囲チェック）
- **requested_at**: 必須、過去〜現在の日時 / 要求日時 / DB（NOT NULL, DEFAULT now()）

---

### audit_logs

#### 概要

- 重要操作の監査証跡（認証/課金/公開停止等）
- **イミュータブル**（INSERT 後の UPDATE/DELETE 禁止）
- **updated_at を持たない、deleted_at を持たない**

#### カラム定義

| column      | type        | null | default           | constraints | description                          |
| ----------- | ----------- | ---- | ----------------- | ----------- | ------------------------------------ |
| id          | uuid        | NO   | gen_random_uuid() | PK          | 監査ログ ID                          |
| action      | varchar(50) | NO   | —                 | —           | アクション種別                       |
| actor_type  | varchar(30) | YES  | —                 | —           | 実行者種別                           |
| actor_id    | uuid        | YES  | —                 | —           | 実行者 ID（FK 無し・イミュータブル） |
| target_type | varchar(30) | YES  | —                 | —           | 対象種別                             |
| target_id   | uuid        | YES  | —                 | —           | 対象 ID                              |
| payload     | jsonb       | YES  | —                 | —           | 追加データ                           |
| ip_address  | varchar(45) | YES  | —                 | —           | IP アドレス                          |
| user_agent  | text        | YES  | —                 | —           | UserAgent                            |
| created_at  | timestamptz | NO   | now()             | —           | 作成日時                             |

#### インデックス一覧

| index_name            | type  | columns/expr                              | where | purpose              |
| --------------------- | ----- | ----------------------------------------- | ----- | -------------------- |
| audit_logs_pkey       | PK    | (id)                                      | —     | 主キー               |
| idx_al_actor_created  | INDEX | (actor_type, actor_id, created_at DESC)   | —     | 実行者別ログ取得     |
| idx_al_target_created | INDEX | (target_type, target_id, created_at DESC) | —     | 対象別ログ取得       |
| idx_al_action_created | INDEX | (action, created_at DESC)                 | —     | アクション種別別ログ |
| idx_al_created        | INDEX | (created_at DESC)                         | —     | 全体時系列ログ       |

#### バリデーションルール

- **action**: 必須、1-50 文字、許可値リストに含まれる / アクション種別 / DB（NOT NULL）、アプリ（enum 値チェック）
- **actor_type**: 任意、許可値：user/creator/admin_user/system / 実行者種別 / アプリ（enum 値チェック）
- **actor_id**: 任意、UUID 形式 / 実行者 ID（FK 無し・イミュータブル） / アプリ
- **target_type**: 任意 / 対象種別 / アプリ
- **target_id**: 任意、UUID 形式 / 対象 ID / アプリ
- **payload**: 任意、有効な JSON 形式 / 追加データ / アプリ（JSON スキーマ検証）
- **ip_address**: 任意、1-45 文字、IPv4 または IPv6 形式 / IP アドレス / アプリ（IP 形式チェック）
- **user_agent**: 任意 / UserAgent / アプリ

**イミュータブル制約**: INSERT 後の UPDATE/DELETE 禁止 → アプリ層 or DB トリガーで制御

---

### notifications

#### 概要

- in-app 通知

#### カラム定義

| column            | type         | null | default           | constraints    | description |
| ----------------- | ------------ | ---- | ----------------- | -------------- | ----------- |
| id                | uuid         | NO   | gen_random_uuid() | PK             | 通知 ID     |
| user_id           | uuid         | NO   | —                 | FK → users(id) | ユーザー ID |
| notification_type | varchar(30)  | NO   | —                 | —              | 通知種別    |
| title             | varchar(100) | YES  | —                 | —              | タイトル    |
| content           | text         | YES  | —                 | —              | 内容        |
| is_read           | boolean      | NO   | false             | —              | 既読フラグ  |
| read_at           | timestamptz  | YES  | —                 | —              | 既読日時    |
| created_at        | timestamptz  | NO   | now()             | —              | 作成日時    |

#### インデックス一覧

| index_name                          | type  | columns/expr                        | where | purpose           |
| ----------------------------------- | ----- | ----------------------------------- | ----- | ----------------- |
| notifications_pkey                  | PK    | (id)                                | —     | 主キー            |
| idx_notifications_user_read_created | INDEX | (user_id, is_read, created_at DESC) | —     | 未読/既読通知一覧 |
| idx_notifications_user_created      | INDEX | (user_id, created_at DESC)          | —     | 全通知一覧        |

#### バリデーションルール

- **user_id**: 必須、存在する users.id を参照 / 通知対象ユーザー / DB（NOT NULL, FK）
- **notification_type**: 必須、1-30 文字、許可値リストに含まれる / 通知種別 / DB（NOT NULL）、アプリ（enum 値チェック）
- **title**: 任意、1-100 文字 / タイトル / アプリ（長さ）
- **content**: 任意、最大 2000 文字 / 内容 / アプリ（長さ）
- **is_read**: 必須、true/false / 既読フラグ / DB（NOT NULL, DEFAULT false）
- **read_at**: ユーザー入力禁止、既読時にサーバー側で自動付与 / 既読日時 / アプリ（既読 API 経由で自動セット）

---

## 3. インデックスまとめ（一覧）

### 3.1 部分 UNIQUE INDEX 一覧

| テーブル             | index_name                     | columns/expr                              | where                                    | 目的                                   |
| -------------------- | ------------------------------ | ----------------------------------------- | ---------------------------------------- | -------------------------------------- |
| users                | users_email_active_uk          | lower(trim(email))                        | deleted_at IS NULL                       | メールアドレス一意性（アクティブのみ） |
| creators             | creators_user_id_active_uk     | user_id                                   | deleted_at IS NULL                       | 1 ユーザー=0..1 クリエイター           |
| admin_users          | admin_users_email_active_uk    | lower(trim(email))                        | deleted_at IS NULL                       | メールアドレス一意性                   |
| character_tags       | character_tags_active_uk       | character_id, tag_id                      | deleted_at IS NULL                       | タグ重複付与防止                       |
| pack_tags            | pack_tags_active_uk            | pack_id, tag_id                           | deleted_at IS NULL                       | タグ重複付与防止                       |
| pack_items           | pack_items_active_uk           | pack_id, item_type, item_id               | deleted_at IS NULL                       | Pack 内重複防止                        |
| user_creator_follows | user_creator_follows_active_uk | user_id, creator_id                       | deleted_at IS NULL                       | 重複フォロー防止                       |
| user_favorites       | user_favorites_active_uk       | user_id, character_id                     | deleted_at IS NULL                       | 重複お気に入り防止                     |
| user_entitlements    | user_entitlements_active_uk    | user_id, entitlement_type, entitlement_id | revoked_at IS NULL                       | 有効な利用権の重複防止                 |
| payout_accounts      | payout_accounts_default_uk     | creator_id                                | is_default = true AND deleted_at IS NULL | デフォルト口座の重複防止               |
| user_blocks          | user_blocks_active_uk          | user_id, target_type, target_id           | deleted_at IS NULL                       | アクティブブロック重複防止             |

### 3.2 通常 UNIQUE INDEX 一覧

| テーブル                     | index_name                               | columns                                         | 目的                       |
| ---------------------------- | ---------------------------------------- | ----------------------------------------------- | -------------------------- |
| m_age_groups                 | m_age_groups_code_key                    | code                                            | コード一意性               |
| m_relationship_stages        | m_relationship_stages_stage_code_key     | stage_code                                      | コード一意性               |
| m_tags                       | m_tags_category_name_key                 | category, name                                  | カテゴリ内タグ名一意性     |
| m_report_reasons             | m_report_reasons_reason_code_key         | reason_code                                     | コード一意性               |
| m_event_types                | m_event_types_type_code_key              | type_code                                       | コード一意性               |
| m_voice_categories           | m_voice_categories_category_code_key     | category_code                                   | コード一意性               |
| m_flag_definitions           | m_flag_definitions_flag_code_key         | flag_code                                       | コード一意性               |
| character_personalities      | character_personalities_character_id_key | character_id                                    | 1:1 関係担保               |
| purchases                    | purchases_payment_uk                     | payment_provider, payment_id                    | 冪等性担保                 |
| user_ticket_balances         | user_ticket_balances_user_id_key         | user_id                                         | 1 ユーザー 1 残高          |
| user_character_relationships | user_character_relationships_uk          | user_id, character_id                           | 同一組み合わせ重複防止     |
| user_character_flags         | user_character_flags_uk                  | user_id, character_id, flag_code                | 同一フラグ重複防止         |
| user_character_memories      | user_character_memories_uk               | user_id, character_id                           | 同一組み合わせ重複防止     |
| rights_consents              | rights_consents_voice_asset_id_key       | voice_asset_id                                  | 1:1 関係担保               |
| user_event_completions       | user_event_completions_uk                | user_id, event_id                               | 重複クリア記録防止         |
| appeals                      | appeals_moderation_action_id_key         | moderation_action_id                            | 0..1 関係担保              |
| terms_agreements             | terms_agreements_uk                      | actor_type, actor_id, terms_type, terms_version | 同一バージョン重複同意防止 |

---

## 4. バリデーションまとめ（一覧）

### 4.1 共通ルール

| ルール                   | 内容                                                                           | 担保        |
| ------------------------ | ------------------------------------------------------------------------------ | ----------- |
| **email 正規化**         | 保存前に trim+lowercase、DB 側でも `lower(trim(email))` で部分 UNIQUE INDEX    | DB ＋アプリ |
| **URL**                  | https のみ、IP 直指定禁止、許可ドメインのみ                                    | アプリ      |
| **enum/status**          | DB CHECK 制約で許可値を縛る                                                    | DB ＋アプリ |
| **論理削除と一意性**     | 部分 UNIQUE INDEX（WHERE deleted_at IS NULL）で担保                            | DB          |
| **ポリモーフィック参照** | 存在チェック＋ deleted_at IS NULL をアプリ層で必須確認                         | アプリ      |
| **監査カラム**           | id/created_at/updated_at/deleted_at はユーザー入力禁止、サーバー側で自動付与   | アプリ      |
| **金額系 CHECK 制約**    | price >= 0, balance >= 0, amount >= 0（※ticket_transactions は例外：符号付き） | DB          |
| **通貨**                 | MVP: JPY 固定。purchases.currency = 'JPY' のみ許可                             | DB          |
| **published 条件**       | packs.status=2(published)時に price NOT NULL を DB で担保                      | DB          |
| **purchases 状態遷移**   | status と purchased_at/refunded_at の整合性を DB CHECK で担保                  | DB          |

### 4.2 ポリモーフィック参照一覧

| テーブル          | type 列          | id 列          | 参照先候補                                  |
| ----------------- | ---------------- | -------------- | ------------------------------------------- |
| pack_items        | item_type        | item_id        | characters, events, voice_packs             |
| user_entitlements | entitlement_type | entitlement_id | packs                                       |
| reports           | target_type      | target_id      | characters, conversation_messages, creators |
| user_blocks       | target_type      | target_id      | users, creators, characters                 |
| terms_agreements  | actor_type       | actor_id       | users, creators, admin_users                |

### 4.3 論理削除の例外テーブル

| テーブル              | 削除方針                     | 理由                     |
| --------------------- | ---------------------------- | ------------------------ |
| conversation_messages | 削除しない（永続保存）       | 会話ログは証跡として保持 |
| audit_logs            | 削除しない（イミュータブル） | 監査ログは改ざん防止     |
| purchases             | 削除しない                   | 会計証跡                 |
| ticket_transactions   | 削除しない                   | 会計証跡                 |

### 4.4 updated_at を持たないテーブル

| テーブル               | 理由                             |
| ---------------------- | -------------------------------- |
| ticket_transactions    | イミュータブルなログ             |
| user_character_flags   | フラグ付与/削除のみ              |
| memory_clips           | 作成のみ                         |
| user_event_completions | クリア記録のみ                   |
| rights_consents        | 同意記録のみ                     |
| terms_agreements       | 同意記録のみ                     |
| payout_line_items      | 明細記録のみ                     |
| conversation_messages  | メッセージログ                   |
| audit_logs             | 監査ログ                         |
| moderation_actions     | 対応記録のみ                     |
| notifications          | 作成と既読のみ（is_read で管理） |

---

## 5. TBD 事項

| 項目               | 内容                                                            |
| ------------------ | --------------------------------------------------------------- |
| 禁止語句リスト     | ユーザー名・キャラ名等で禁止する語句の定義                      |
| 許可ドメインリスト | 画像 URL・ファイル URL 等で許可するドメインの定義               |
| JSON スキーマ      | personality_data, bank_info, preferences 等の必須キー・構造定義 |
| 金額上限           | price, amount 等の上限値                                        |
| 好感度上限         | affection_points の上限値                                       |
| 署名付き URL       | ファイルダウンロード系の署名付き URL 運用方針                   |
| 多通貨対応         | 将来的に USD 等へ拡張する場合の currency カラム追加方針         |

---

## 改訂履歴

| バージョン | 日付       | 変更内容                                                                                          |
| ---------- | ---------- | ------------------------------------------------------------------------------------------------- |
| 1.0.0      | 2026-01-31 | 初版作成（Step2〜Step4 を統合）                                                                   |
|            |            | - packs テーブルに creator_id を追加（所有者の確定）                                              |
|            |            | - CHECK 制約追加：packs.price, purchases.amount, creator_payouts.amount, payout_line_items.amount |
| 1.0.1      | 2026-01-31 | CRITICAL/IMPORTANT 修正                                                                           |
|            |            | - 通貨方針：MVP JPY 固定（purchases.currency = 'JPY' のみ）、1.6 節追加                           |
|            |            | - ticket_transactions.amount：符号付き CHECK 制約追加（金額系 >= 0 の例外）                       |
|            |            | - purchases.refunded_at カラム追加（status=3 時は必須）                                           |
|            |            | - packs: CHECK (status <> 2 OR price IS NOT NULL) 追加（published 条件の堅牢化）                  |
| 1.0.2      | 2026-01-31 | purchases 状態遷移の堅牢化                                                                        |
|            |            | - purchases: status と purchased_at/refunded_at の整合性を DB CHECK で担保                        |
|            |            | - 状態遷移ルール表を追加（pending/completed/refunded ごとの日時制約）                             |
|            |            | - 監査カラムの例外テーブル（updated_at を持たないテーブル）を整理                                 |
