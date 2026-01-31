# AI will エンティティ一覧（v3.1.8）

| 項目 | 内容 |
|------|------|
| ドキュメント名 | AI will エンティティ一覧 |
| バージョン | 3.1.8 |
| 作成日 | 2026-01-31 |
| 最終更新日 | 2026-01-31 |
| ステータス | ドラフト |

---

## 目次

1. [マスタデータ（master）](#1-マスタデータmaster)
2. [トランザクションデータ（transaction）](#2-トランザクションデータtransaction)
   - 2.1 [ユーザー/アカウント系](#21-ユーザーアカウント系)
   - 2.2 [キャラクター系](#22-キャラクター系)
   - 2.3 [商品/販売単位系](#23-商品販売単位系)
   - 2.4 [フォロー/お気に入り系](#24-フォローお気に入り系)
   - 2.5 [課金/決済系](#25-課金決済系)
   - 2.6 [収益分配系](#26-収益分配系)
   - 2.7 [ユーザー×キャラクター関係系](#27-ユーザーキャラクター関係系)
   - 2.8 [音声系](#28-音声系)
   - 2.9 [イベント系](#29-イベント系)
   - 2.10 [会話系](#210-会話系)
   - 2.11 [通報/モデレーション/安全系](#211-通報モデレーション安全系)
   - 2.12 [権利/同意系](#212-権利同意系)
   - 2.13 [プライバシー系](#213-プライバシー系)
   - 2.14 [ログ/通知系](#214-ログ通知系)

---

## 1. マスタデータ（master）

参照用の固定データで、変更頻度が低いテーブル群。

| エンティティ名 | テーブル名 | 種類 | 主キー | 説明 |
|---------------|-----------|------|--------|------|
| 年齢区分マスタ | `m_age_groups` | master | `id` (uuid) | ユーザーの年齢区分定義（u13/u18/adult等）。**任意（将来拡張用）**。MVPではアプリ側定数でも可 |
| 関係ステージマスタ | `m_relationship_stages` | master | `id` (uuid) | 好感度に応じた関係性の段階定義（初対面→知り合い→友達→仲良し→恋人等）。`stage_code` は UNIQUE |
| タグマスタ | `m_tags` | master | `id` (uuid) | キャラクター/Pack分類用のタグ（ジャンル、属性等） |
| 通報理由マスタ | `m_report_reasons` | master | `id` (uuid) | 通報時に選択する理由の選択肢。`reason_code` は UNIQUE |
| イベント種別マスタ | `m_event_types` | master | `id` (uuid) | イベントの種別定義（1回きり/周回可/状態変化等）。MVPではenum運用も可 |
| 音声カテゴリマスタ | `m_voice_categories` | master | `id` (uuid) | 音声素材の分類（相槌/挨拶/イベントセリフ等）。`category_code` は UNIQUE |
| フラグ定義マスタ | `m_flag_definitions` | master | `id` (uuid) | イベント解放等に使う状態フラグの定義。`flag_code` は UNIQUE（FK参照元） |

---

## 2. トランザクションデータ（transaction）

業務で発生し増加し続けるテーブル群。追加/更新/削除が多い。

### 2.1 ユーザー/アカウント系

| エンティティ名 | テーブル名 | 種類 | 主キー | 説明 |
|---------------|-----------|------|--------|------|
| ユーザー | `users` | transaction | `id` (uuid) | エンドユーザーのアカウント情報。`age_group`（VARCHAR）で年齢区分を保持 |
| クリエイター | `creators` | transaction | `id` (uuid) | キャラクター作成者のアカウント。`user_id` は UNIQUE（1ユーザー=0..1クリエイター） |
| 運営ユーザー | `admin_users` | transaction | `id` (uuid) | 運営/モデレーターのアカウント。`role` で権限を区別 |

### 2.2 キャラクター系

| エンティティ名 | テーブル名 | 種類 | 主キー | 説明 |
|---------------|-----------|------|--------|------|
| キャラクター | `characters` | transaction | `id` (uuid) | クリエイターが作成したキャラクターの基本情報。単体販売せず必ずPack経由で販売 |
| キャラクター人格設定 | `character_personalities` | transaction | `id` (uuid) | キャラクターの性格・口調・世界観等の設定。`character_id` → `characters.id`（NOT NULL, UNIQUE）で1:1。MVPなら `characters` にJSON埋め込みも可 |

### 2.3 商品/販売単位系

| エンティティ名 | テーブル名 | 種類 | 主キー | 説明 |
|---------------|-----------|------|--------|------|
| Pack（商品） | `packs` | transaction | `id` (uuid) | Persona Pack / Scenario Pack 等の販売単位。`pack_type` で種別を区別 |
| Pack構成アイテム | `pack_items` | transaction | `id` (uuid) | Packに含まれるコンテンツ。**ポリモーフィック参照**（`item_type` + `item_id`）。FK無し、アプリ層で存在チェック必須 |
| キャラクタータグ中間 | `character_tags` | transaction | `id` (uuid) | キャラクターとタグの紐付け（多対多）。`UNIQUE (character_id, tag_id)` |
| Packタグ中間 | `pack_tags` | transaction | `id` (uuid) | Packとタグの紐付け（多対多）。`UNIQUE (pack_id, tag_id)` |

### 2.4 フォロー/お気に入り系

| エンティティ名 | テーブル名 | 種類 | 主キー | 説明 |
|---------------|-----------|------|--------|------|
| クリエイターフォロー | `user_creator_follows` | transaction | `id` (uuid) | ユーザーによるクリエイターのフォロー。`UNIQUE (user_id, creator_id)` |
| お気に入り | `user_favorites` | transaction | `id` (uuid) | ユーザーがお気に入り登録したキャラクター。`UNIQUE (user_id, character_id)` |

### 2.5 課金/決済系

| エンティティ名 | テーブル名 | 種類 | 主キー | 説明 |
|---------------|-----------|------|--------|------|
| 購入履歴 | `purchases` | transaction | `id` (uuid) | 決済記録（Source of Truth）。`UNIQUE (payment_provider, payment_id)` で冪等性担保。返金時は `user_entitlements` をrevoke |
| 利用権 | `user_entitlements` | transaction | `id` (uuid) | ユーザーが保持する利用権（購入/無料付与/復元）。`source_purchase_id` で購入と紐付け。`UNIQUE (user_id, entitlement_type, entitlement_id) WHERE revoked_at IS NULL` |
| チケット残高 | `user_ticket_balances` | transaction | `id` (uuid) | ユーザーのチケット/クレジット残高（キャッシュ）。`UNIQUE (user_id)`。`ticket_transactions` から再計算可能 |
| チケット取引 | `ticket_transactions` | transaction | `id` (uuid) | チケットの購入・消費履歴（Source of Truth）。`transaction_type`: purchase/consume/refund/grant |

### 2.6 収益分配系

| エンティティ名 | テーブル名 | 種類 | 主キー | 説明 |
|---------------|-----------|------|--------|------|
| 振込口座 | `payout_accounts` | transaction | `id` (uuid) | クリエイターの振込先情報。`is_default` + `deleted_at` でデフォルト口座を管理 |
| クリエイター支払い | `creator_payouts` | transaction | `id` (uuid) | クリエイターへの収益分配記録。期間ごとの集計・支払い |
| 支払い明細 | `payout_line_items` | transaction | `id` (uuid) | 分配対象の売上明細。`payout_id` に紐づく内訳 |

### 2.7 ユーザー×キャラクター関係系

| エンティティ名 | テーブル名 | 種類 | 主キー | 説明 |
|---------------|-----------|------|--------|------|
| ユーザー×キャラ関係 | `user_character_relationships` | transaction | `id` (uuid) | ユーザーとキャラクターの好感度・関係ステージ。`stage_id` → `m_relationship_stages`。`UNIQUE (user_id, character_id)` |
| ユーザー×キャラ×フラグ | `user_character_flags` | transaction | `id` (uuid) | ユーザー×キャラ単位の状態フラグ（告白済み等）。`flag_code` → `m_flag_definitions.flag_code`（FK）。`UNIQUE (user_id, character_id, flag_code)` |
| ユーザー×キャラ長期記憶 | `user_character_memories` | transaction | `id` (uuid) | ユーザーの呼び方、好み、NG、会話要約等。`UNIQUE (user_id, character_id)` |
| 切り抜きメモリー | `memory_clips` | transaction | `id` (uuid) | ユーザーが保存した会話の切り抜き。`user_id` → `users.id`（NOT NULL）、`character_id` → `characters.id`（NOT NULL）、`source_message_id` → `conversation_messages.id`（NULL可） |

### 2.8 音声系

| エンティティ名 | テーブル名 | 種類 | 主キー | 説明 |
|---------------|-----------|------|--------|------|
| ボイスパック | `voice_packs` | transaction | `id` (uuid) | 音声素材のセット（メタ情報）。`character_id` に紐づく |
| 音声アセット | `voice_assets` | transaction | `id` (uuid) | 個別の音声ファイル実体。`voice_pack_id` → `voice_packs.id`（NOT NULL）、`voice_category_id` → `m_voice_categories` |
| 権利宣誓/同意 | `rights_consents` | transaction | `id` (uuid) | 音声アップロード時の権利同意・宣誓記録。`voice_asset_id` と1:1（`UNIQUE (voice_asset_id)`） |

### 2.9 イベント系

| エンティティ名 | テーブル名 | 種類 | 主キー | 説明 |
|---------------|-----------|------|--------|------|
| イベント | `events` | transaction | `id` (uuid) | キャラクターに紐づく特別イベントの定義（告白、記念日等）。`character_id` → `characters.id`（NOT NULL）、`event_type_id` → `m_event_types.id`（NULL可, **※暫定・要確認**） |
| イベント解放条件 | `event_unlock_conditions` | transaction | `id` (uuid) | イベント解放に必要な条件。`condition_type`: flag/affection/event_completed。`event_id` → `events.id`（NOT NULL）、`prerequisite_event_id` → `events.id`（NULL可）、`flag_code` → `m_flag_definitions`（NULL可）。排他CHECK制約あり |
| イベント台本ノード | `event_script_nodes` | transaction | `id` (uuid) | イベント台本のセリフ・選択肢・分岐定義。`event_id` → `events.id`（NOT NULL）、`voice_asset_id` → `voice_assets.id`（NULL可） |
| イベント分岐選択肢 | `event_branch_options` | transaction | `id` (uuid) | 分岐ノードの選択肢と遷移先。`node_id` → `event_script_nodes.id`（NOT NULL）、`next_node_id` → `event_script_nodes.id`（NULL可）で次ノードを参照 |
| イベントクリア履歴 | `user_event_completions` | transaction | `id` (uuid) | ユーザーがクリアしたイベントの記録。`UNIQUE (user_id, event_id)` |

### 2.10 会話系

| エンティティ名 | テーブル名 | 種類 | 主キー | 説明 |
|---------------|-----------|------|--------|------|
| 会話セッション | `conversation_sessions` | transaction | `id` (uuid) | ユーザーとキャラクターの会話単位。`user_id` → `users.id`（NOT NULL）、`character_id` → `characters.id`（NOT NULL）、`session_type`: free/event、`event_id` → `events.id`（NULL可）でイベント会話を紐付け |
| 会話メッセージ | `conversation_messages` | transaction | `id` (uuid) | 会話内の個別発話・応答ログ。`session_id` → `conversation_sessions.id`（NOT NULL）、`role`: user/character |

### 2.11 通報/モデレーション/安全系

| エンティティ名 | テーブル名 | 種類 | 主キー | 説明 |
|---------------|-----------|------|--------|------|
| 通報 | `reports` | transaction | `id` (uuid) | ユーザーからの通報内容。`reporter_user_id` → `users.id`（NULL可、退会時SET NULL）、`reason_id` → `m_report_reasons.id`（NOT NULL）、**ポリモーフィック参照**（`target_type` + `target_id`）。`status`: open/in_progress/resolved/rejected |
| モデレーション対応 | `moderation_actions` | transaction | `id` (uuid) | 運営による対応記録（公開停止等）。`report_id` → `reports.id`（NULL可、通報起因でない場合あり）、`admin_user_id` → `admin_users.id`（NOT NULL）、`action_type`: suspend/restore/warn/ban |
| 異議申し立て | `appeals` | transaction | `id` (uuid) | クリエイターからの異議申し立て。`UNIQUE (moderation_action_id)` で0..1関係を担保 |
| ブロック | `user_blocks` | transaction | `id` (uuid) | ユーザーによるブロック設定。**ポリモーフィック参照**（`target_type` + `target_id`）。`UNIQUE (user_id, target_type, target_id) WHERE deleted_at IS NULL` |

### 2.12 権利/同意系

| エンティティ名 | テーブル名 | 種類 | 主キー | 説明 |
|---------------|-----------|------|--------|------|
| 規約同意 | `terms_agreements` | transaction | `id` (uuid) | ユーザー/クリエイター/運営の規約同意記録。**ポリモーフィック参照**（`actor_type` + `actor_id`）。`UNIQUE (actor_type, actor_id, terms_type, terms_version)` |

### 2.13 プライバシー系

| エンティティ名 | テーブル名 | 種類 | 主キー | 説明 |
|---------------|-----------|------|--------|------|
| データ削除要求 | `data_deletion_requests` | transaction | `id` (uuid) | ユーザーからのデータ削除要求とその対応状況。`status`: requested/processing/completed/rejected |
| データエクスポート要求 | `data_export_requests` | transaction | `id` (uuid) | ユーザーからのデータエクスポート要求。`status`: requested/processing/ready/expired |

### 2.14 ログ/通知系

| エンティティ名 | テーブル名 | 種類 | 主キー | 説明 |
|---------------|-----------|------|--------|------|
| 監査ログ | `audit_logs` | transaction | `id` (uuid) | 重要操作の監査証跡（認証/課金/公開停止等）。書き込み専用、改ざん防止 |
| 通知 | `notifications` | transaction | `id` (uuid) | in-app通知（任意実装）。プッシュ通知のみなら外部サービスで管理し、このテーブルは不要 |

---

## 補足：ポリモーフィック参照のテーブル一覧

以下のテーブルはポリモーフィック参照（`type` + `id` の組み合わせで参照先を動的に決定）を採用しており、DBのFK制約が張れません。アプリ層での存在チェックが必須です。

| テーブル名 | ポリモーフィックカラム | 参照先 |
|-----------|---------------------|--------|
| `pack_items` | `item_type`, `item_id` | characters / events / voice_packs |
| `user_entitlements` | `entitlement_type`, `entitlement_id` | packs（MVP）/ 将来：subscription等 |
| `reports` | `target_type`, `target_id` | characters / conversation_messages / creators 等 |
| `user_blocks` | `target_type`, `target_id` | users / creators / characters |
| `terms_agreements` | `actor_type`, `actor_id` | users / creators / admin_users |

※ `user_entitlements` はMVPでは `entitlement_type='pack'` のみ運用想定。将来の拡張（subscription等）のため type カラムを残している。

---

## 補足：主要なUNIQUE制約一覧

| テーブル名 | UNIQUE制約 | 目的 |
|-----------|-----------|------|
| `creators` | `(user_id)` | 1ユーザー=0..1クリエイター |
| `character_personalities` | `(character_id)` | 1キャラ=1人格設定（1:1） |
| `purchases` | `(payment_provider, payment_id)` | 決済の冪等性 |
| `user_entitlements` | `(user_id, entitlement_type, entitlement_id) WHERE revoked_at IS NULL` | 有効な利用権の重複防止 |
| `user_ticket_balances` | `(user_id)` | 1ユーザー1残高 |
| `pack_items` | `(pack_id, item_type, item_id)` | Pack内重複防止 |
| `character_tags` | `(character_id, tag_id)` | タグ重複防止 |
| `pack_tags` | `(pack_id, tag_id)` | タグ重複防止 |
| `user_creator_follows` | `(user_id, creator_id)` | フォロー重複防止 |
| `user_favorites` | `(user_id, character_id)` | お気に入り重複防止 |
| `user_character_relationships` | `(user_id, character_id)` | 関係レコード重複防止 |
| `user_character_flags` | `(user_id, character_id, flag_code)` | フラグ重複防止 |
| `user_character_memories` | `(user_id, character_id)` | 記憶レコード重複防止 |
| `user_event_completions` | `(user_id, event_id)` | クリア履歴重複防止 |
| `rights_consents` | `(voice_asset_id)` | 1:1関係担保 |
| `appeals` | `(moderation_action_id)` | 0..1関係担保 |
| `user_blocks` | `(user_id, target_type, target_id) WHERE deleted_at IS NULL` | アクティブなブロック重複防止 |
| `terms_agreements` | `(actor_type, actor_id, terms_type, terms_version)` | 同一バージョン重複同意防止 |

---

## 改訂履歴

| バージョン | 日付 | 変更内容 | 担当者 |
|------------|------|----------|--------|
| 3.1.7 | 2026-01-31 | 初版作成（v3.1.7時点のエンティティを反映） | - |
| 3.1.8 | 2026-01-31 | 重要FK列を明示: voice_assets.voice_pack_id, event_script_nodes.event_id, event_branch_options.node_id, memory_clips.user_id/character_id, conversation_sessions.user_id/character_id, conversation_messages.session_id, reports.reporter_user_id/reason_id, moderation_actions.report_id/admin_user_id, character_personalities.character_id(UNIQUE), events.character_id/event_type_id(暫定) | - |

---

*本ドキュメントは AI will データベース設計のエンティティ一覧です。詳細なカラム定義・制約・ER図は別途「エンティティ関係整理」ドキュメントを参照してください。*
