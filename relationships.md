# AI will リレーションシップ設計（v1.0.2）

| 項目 | 内容 |
|------|------|
| ドキュメント名 | AI will リレーションシップ設計 |
| バージョン | 1.0.2 |
| 作成日 | 2026-01-31 |
| 最終更新日 | 2026-01-31 |
| 参照元 | entities.md v3.1.8 |
| ステータス | ドラフト |
| **DB前提** | **PostgreSQL**。部分UNIQUE INDEX（WHERE句付き）等を使用。MySQLの場合は代替実装が必要 |

---

## 目次

1. [1対1リレーション](#1-1対1リレーション)
2. [1対多リレーション](#2-1対多リレーション)
3. [多対多リレーション（中間テーブル）](#3-多対多リレーション中間テーブル)
4. [ポリモーフィック参照（FK制約なし）](#4-ポリモーフィック参照fk制約なし)
5. [複合UNIQUE制約一覧](#5-複合unique制約一覧)
6. [部分UNIQUE制約一覧（条件付き一意）](#6-部分unique制約一覧条件付き一意)
7. [制約矛盾チェック結果](#7-制約矛盾チェック結果)
8. [仮定一覧](#8-仮定一覧)
9. [未確定事項（質問）](#9-未確定事項質問)

---

## 1. 1対1リレーション

| 親テーブル | 子テーブル | FK列（子側） | NULL可否 | UNIQUE | ON DELETE | 理由 |
|------------|------------|--------------|----------|--------|-----------|------|
| `users` | `creators` | `user_id` | NOT NULL | YES | RESTRICT | クリエイター削除前にキャラクター等の移管/削除が必要 |
| `characters` | `character_personalities` | `character_id` | NOT NULL | YES | CASCADE | 人格設定はキャラクターの一部、親削除で不要 |
| `voice_assets` | `rights_consents` | `voice_asset_id` | NOT NULL | YES | CASCADE | 権利同意は音声アセットの付帯情報 |
| `moderation_actions` | `appeals` | `moderation_action_id` | NOT NULL | YES | CASCADE | 異議申し立ては対応記録の付帯情報 |
| `users` | `user_ticket_balances` | `user_id` | NOT NULL | YES | CASCADE | 残高はユーザー削除時に不要 |

---

## 2. 1対多リレーション

### 2.1 ユーザー/アカウント系

| 親テーブル | 子テーブル | FK列（子側） | NULL可否 | ON DELETE | 理由 |
|------------|------------|--------------|----------|-----------|------|
| `users` | `purchases` | `user_id` | NOT NULL | RESTRICT | 購入履歴は会計証跡、削除前に精査必要 |
| `users` | `user_entitlements` | `user_id` | NOT NULL | RESTRICT | 利用権履歴は証跡として保持 |
| `users` | `ticket_transactions` | `user_id` | NOT NULL | RESTRICT | チケット取引履歴は会計証跡 |
| `users` | `conversation_sessions` | `user_id` | NOT NULL | CASCADE | **暫定**: 退会時に削除（**要確認**: 物理/論理削除方針） |
| `users` | `data_deletion_requests` | `user_id` | NOT NULL | RESTRICT | 削除要求の処理完了まで保持 |
| `users` | `data_export_requests` | `user_id` | NOT NULL | RESTRICT | エクスポート要求の処理完了まで保持 |
| `users` | `reports` | `reporter_user_id` | NULL | SET NULL | 通報者が退会しても通報記録は残す |
| `users` | `notifications` | `user_id` | NOT NULL | CASCADE | 通知はユーザー削除時に不要 |
| `users` | `memory_clips` | `user_id` | NOT NULL | CASCADE | 切り抜きはユーザー削除時に不要 |

### 2.2 クリエイター系

| 親テーブル | 子テーブル | FK列（子側） | NULL可否 | ON DELETE | 理由 |
|------------|------------|--------------|----------|-----------|------|
| `creators` | `characters` | `creator_id` | NOT NULL | RESTRICT | キャラクターが残っている間は削除不可 |
| `creators` | `payout_accounts` | `creator_id` | NOT NULL | CASCADE | 振込口座はクリエイター削除時に不要 |
| `creators` | `creator_payouts` | `creator_id` | NOT NULL | RESTRICT | 支払い履歴は会計証跡 |

### 2.3 キャラクター系

| 親テーブル | 子テーブル | FK列（子側） | NULL可否 | ON DELETE | 理由 |
|------------|------------|--------------|----------|-----------|------|
| `characters` | `events` | `character_id` | NOT NULL | CASCADE | キャラクター削除時にイベントも削除 |
| `characters` | `voice_packs` | `character_id` | NOT NULL | CASCADE | 音声パックはキャラクターに従属 |
| `characters` | `conversation_sessions` | `character_id` | NOT NULL | CASCADE | **暫定**: キャラ削除時に会話も削除（**要確認**: 削除ポリシー） |
| `characters` | `memory_clips` | `character_id` | NOT NULL | CASCADE | キャラクター削除時に切り抜きも削除 |

### 2.4 商品/販売系

| 親テーブル | 子テーブル | FK列（子側） | NULL可否 | ON DELETE | 理由 |
|------------|------------|--------------|----------|-----------|------|
| `packs` | `pack_items` | `pack_id` | NOT NULL | CASCADE | Pack削除時に構成アイテムも削除 |
| `purchases` | `user_entitlements` | `source_purchase_id` | NULL | SET NULL | 無料付与の場合NULL、返金時はrevoke処理 |

### 2.5 音声系

| 親テーブル | 子テーブル | FK列（子側） | NULL可否 | ON DELETE | 理由 |
|------------|------------|--------------|----------|-----------|------|
| `voice_packs` | `voice_assets` | `voice_pack_id` | NOT NULL | CASCADE | 音声アセットはパックに従属 |
| `m_voice_categories` | `voice_assets` | `voice_category_id` | NOT NULL | RESTRICT | カテゴリが使用中なら削除不可 |

### 2.6 イベント系

| 親テーブル | 子テーブル | FK列（子側） | NULL可否 | ON DELETE | 理由 |
|------------|------------|--------------|----------|-----------|------|
| `events` | `event_unlock_conditions` | `event_id` | NOT NULL | CASCADE | イベント削除時に条件も削除 |
| `events` | `event_unlock_conditions` | `prerequisite_event_id` | NULL | SET NULL | 前提イベント削除時はNULLに（条件緩和） |
| `events` | `event_script_nodes` | `event_id` | NOT NULL | CASCADE | イベント削除時に台本も削除 |
| `events` | `conversation_sessions` | `event_id` | NULL | SET NULL | イベント削除後も会話ログは残す |
| `event_script_nodes` | `event_branch_options` | `node_id` | NOT NULL | CASCADE | ノード削除時に選択肢も削除 |
| `event_script_nodes` | `event_branch_options` | `next_node_id` | NULL | SET NULL | 遷移先ノード削除時はNULLに |
| `voice_assets` | `event_script_nodes` | `voice_asset_id` | NULL | SET NULL | 音声削除後もノードは残す |
| `m_event_types` | `events` | `event_type_id` | NULL | RESTRICT | マスタ使用中なら削除不可（※仮定）**【暫定・要確認】NULL可否は仕様に直結** |
| `m_flag_definitions` | `event_unlock_conditions` | `flag_code` | NULL | RESTRICT | フラグ定義使用中なら削除不可 |

### 2.7 会話系

| 親テーブル | 子テーブル | FK列（子側） | NULL可否 | ON DELETE | 理由 |
|------------|------------|--------------|----------|-----------|------|
| `conversation_sessions` | `conversation_messages` | `session_id` | NOT NULL | CASCADE | セッション削除時にメッセージも削除 |
| `conversation_messages` | `memory_clips` | `source_message_id` | NULL | SET NULL | 元メッセージ削除後も切り抜きは残す |

### 2.8 収益分配系

| 親テーブル | 子テーブル | FK列（子側） | NULL可否 | ON DELETE | 理由 |
|------------|------------|--------------|----------|-----------|------|
| `creator_payouts` | `payout_line_items` | `payout_id` | NOT NULL | RESTRICT | 明細は支払い記録の証跡 |

### 2.9 通報/モデレーション系

| 親テーブル | 子テーブル | FK列（子側） | NULL可否 | ON DELETE | 理由 |
|------------|------------|--------------|----------|-----------|------|
| `m_report_reasons` | `reports` | `reason_id` | NOT NULL | RESTRICT | 理由マスタ使用中なら削除不可 |
| `reports` | `moderation_actions` | `report_id` | NULL | SET NULL | 通報削除後も対応記録は残す |
| `admin_users` | `moderation_actions` | `admin_user_id` | NOT NULL | RESTRICT | 対応者が退職前に引き継ぎ必要 |

### 2.10 マスタ → トランザクション

| 親テーブル | 子テーブル | FK列（子側） | NULL可否 | ON DELETE | 理由 |
|------------|------------|--------------|----------|-----------|------|
| `m_relationship_stages` | `user_character_relationships` | `stage_id` | NOT NULL | RESTRICT | マスタ使用中なら削除不可 |
| `m_flag_definitions` | `user_character_flags` | `flag_code` | NOT NULL | RESTRICT | フラグ定義使用中なら削除不可 |
| `m_tags` | `character_tags` | `tag_id` | NOT NULL | RESTRICT | タグ使用中なら削除不可 |
| `m_tags` | `pack_tags` | `tag_id` | NOT NULL | RESTRICT | タグ使用中なら削除不可 |

---

## 3. 多対多リレーション（中間テーブル）

### 3.1 純粋な多対多

| テーブルA | 中間テーブル | テーブルB | FK列(A) | FK列(B) | 複合UNIQUE | ON DELETE(A) | ON DELETE(B) | 理由 |
|-----------|--------------|-----------|---------|---------|------------|--------------|--------------|------|
| `characters` | `character_tags` | `m_tags` | `character_id` | `tag_id` | `(character_id, tag_id)` | CASCADE | RESTRICT | キャラ削除で紐付け解除、タグは使用中削除不可 |
| `packs` | `pack_tags` | `m_tags` | `pack_id` | `tag_id` | `(pack_id, tag_id)` | CASCADE | RESTRICT | Pack削除で紐付け解除、タグは使用中削除不可 |
| `users` | `user_creator_follows` | `creators` | `user_id` | `creator_id` | `(user_id, creator_id)` | CASCADE | CASCADE | どちら削除でもフォロー解除 |
| `users` | `user_favorites` | `characters` | `user_id` | `character_id` | `(user_id, character_id)` | CASCADE | CASCADE | どちら削除でもお気に入り解除 |

### 3.2 追加属性を持つ関連テーブル

| テーブルA | 中間テーブル | テーブルB | FK列(A) | FK列(B) | 複合UNIQUE | ON DELETE(A) | ON DELETE(B) | 備考 |
|-----------|--------------|-----------|---------|---------|------------|--------------|--------------|------|
| `users` | `user_character_relationships` | `characters` | `user_id` | `character_id` | `(user_id, character_id)` | CASCADE | CASCADE | 好感度・ステージを保持 |
| `users` | `user_character_flags` | `characters` | `user_id` | `character_id` | `(user_id, character_id, flag_code)` | CASCADE | CASCADE | flag_codeも複合UNIQUEに含む |
| `users` | `user_character_memories` | `characters` | `user_id` | `character_id` | `(user_id, character_id)` | CASCADE | CASCADE | 呼び方・好み・NG等を保持 |
| `users` | `user_event_completions` | `events` | `user_id` | `event_id` | `(user_id, event_id)` | CASCADE | CASCADE | クリア日時等を保持 |
| `users` | `user_blocks` | (ポリモーフィック) | `user_id` | - | `(user_id, target_type, target_id) WHERE deleted_at IS NULL` | CASCADE | (アプリ層) | ブロック者削除で解除 |

---

## 4. ポリモーフィック参照（FK制約なし）

以下はDBレベルのFK制約を張れないため、**アプリ層での存在チェック・削除処理が必須**。

| テーブル | Type列 | ID列 | 参照先候補 | 削除時の処理 |
|----------|--------|------|------------|--------------|
| `pack_items` | `item_type` | `item_id` | characters / events / voice_packs | 参照先削除時にアプリ層で pack_items も削除 |
| `user_entitlements` | `entitlement_type` | `entitlement_id` | packs（MVP）/ subscription等 | 参照先削除時にアプリ層で revoke 処理 |

> ### ⚠️ 重要注意: packs の物理削除について
>
> `user_entitlements` は `packs` をポリモーフィック参照（FK制約なし）しているため、**packs を物理削除すると以下の問題が発生する**:
>
> 1. **購入者の利用権が参照先を失う**（entitlement_id が孤立IDになる）
> 2. **購入履歴の整合性が崩れる**（何を購入したか不明になる）
> 3. **返金・サポート対応が困難になる**
>
> **推奨方針**: `packs` は物理削除せず、`status` カラム（例: `active` / `archived` / `deleted`）で論理管理する。販売停止は `status='archived'` で対応し、既存購入者の利用権は維持する。
| `reports` | `target_type` | `target_id` | characters / conversation_messages / creators | 参照先削除時に SET NULL 相当の処理 |
| `user_blocks` | `target_type` | `target_id` | users / creators / characters | 参照先削除時にアプリ層で削除 |
| `terms_agreements` | `actor_type` | `actor_id` | users / creators / admin_users | 同意記録は保持、actor削除でも残す |

---

## 5. 複合UNIQUE制約一覧

### 5.1 中間テーブル用

| テーブル | 複合UNIQUE列 | 目的 |
|----------|--------------|------|
| `character_tags` | `(character_id, tag_id)` | 同一タグの重複付与防止 |
| `pack_tags` | `(pack_id, tag_id)` | 同一タグの重複付与防止 |
| `user_creator_follows` | `(user_id, creator_id)` | 重複フォロー防止 |
| `user_favorites` | `(user_id, character_id)` | 重複お気に入り防止 |
| `user_character_relationships` | `(user_id, character_id)` | 同一組み合わせの重複防止 |
| `user_character_flags` | `(user_id, character_id, flag_code)` | 同一フラグの重複防止 |
| `user_character_memories` | `(user_id, character_id)` | 同一組み合わせの重複防止 |
| `user_event_completions` | `(user_id, event_id)` | 同一イベントの重複クリア記録防止 |

### 5.2 ビジネスルール用

| テーブル | 複合UNIQUE列 | 目的 |
|----------|--------------|------|
| `purchases` | `(payment_provider, payment_id)` | 決済の冪等性担保 |
| `pack_items` | `(pack_id, item_type, item_id)` | Pack内同一アイテム重複防止 |
| `terms_agreements` | `(actor_type, actor_id, terms_type, terms_version)` | 同一バージョン規約への重複同意防止 |

### 5.3 マスタデータのコード一意性

| テーブル | UNIQUE列 | 目的 |
|----------|----------|------|
| `m_relationship_stages` | `(stage_code)` | ステージコードの一意性 |
| `m_report_reasons` | `(reason_code)` | 理由コードの一意性 |
| `m_voice_categories` | `(category_code)` | カテゴリコードの一意性 |
| `m_flag_definitions` | `(flag_code)` | フラグコードの一意性 |

---

## 6. 部分UNIQUE制約一覧（条件付き一意）

| テーブル | 部分UNIQUE列 | 条件 | 目的 |
|----------|--------------|------|------|
| `user_entitlements` | `(user_id, entitlement_type, entitlement_id)` | `WHERE revoked_at IS NULL` | 有効な利用権の重複防止 |
| `user_blocks` | `(user_id, target_type, target_id)` | `WHERE deleted_at IS NULL` | アクティブなブロックの重複防止 |
| `payout_accounts` | `(creator_id)` | `WHERE is_default = true AND deleted_at IS NULL` | デフォルト口座の重複防止（※仮定） |

---

## 7. 制約矛盾チェック結果

### 7.1 ON DELETE SET NULL × NOT NULL の矛盾

| テーブル | FK列 | 現設計 | 問題 | 修正案 |
|----------|------|--------|------|--------|
| - | - | - | **矛盾なし** | - |

**結果**: 本設計では SET NULL を指定した FK列はすべて NULL 許可としているため、矛盾はありません。

### 7.2 CASCADE連鎖リスクの確認

| 起点 | 連鎖先 | リスク | 対策案 |
|------|--------|--------|--------|
| `users` | `conversation_sessions` → `conversation_messages` | 大量削除 | 論理削除への変更を検討 |
| `characters` | `events` → `event_script_nodes` → `event_branch_options` | 中規模削除 | キャラクター単位で完結するため許容可 |
| `characters` | `voice_packs` → `voice_assets` → `rights_consents` | 中規模削除 | キャラクター単位で完結するため許容可 |

---

## 8. 仮定一覧

以下は `entities.md` に明示されていないため、仮定として設計に含めています。

| # | 仮定内容 | 根拠・理由 | ステータス |
|---|----------|------------|------------|
| 1 | `voice_assets` に `voice_pack_id` (FK) が存在する | `voice_packs` と `voice_assets` の親子関係が必要 | ✅ **entities.md v3.1.8 に明示済み** |
| 2 | `events` に `event_type_id` (FK, NULL可) が存在する | `m_event_types` マスタが定義されているが、`events` への参照列は未記載 | 仮定（要確認） |
| 3 | `reports` に `reason_id` (FK) が存在する | `m_report_reasons` マスタが定義されている | ✅ **entities.md v3.1.8 に明示済み** |
| 4 | `reports` に `reporter_user_id` (FK, NULL可) が存在する | 通報者を特定するFKが必要 | ✅ **entities.md v3.1.8 に明示済み** |
| 5 | `moderation_actions` に `report_id` (FK, NULL可) が存在する | 通報起因でない対応もあり得るためNULL可 | ✅ **entities.md v3.1.8 に明示済み** |
| 6 | `moderation_actions` に `admin_user_id` (FK) が存在する | 対応者を特定するFKが必要 | ✅ **entities.md v3.1.8 に明示済み** |
| 7 | `event_script_nodes` に `event_id` (FK) が存在する | イベントと台本ノードの親子関係が必要 | ✅ **entities.md v3.1.8 に明示済み** |
| 8 | `event_branch_options` に `node_id` (FK) が存在する | 台本ノードと分岐選択肢の親子関係が必要 | ✅ **entities.md v3.1.8 に明示済み** |
| 9 | `character_personalities.character_id` は UNIQUE | 1キャラ=1人格設定の1:1関係 | ✅ **entities.md v3.1.8 に明示済み** |
| 10 | `memory_clips` に `user_id` と `character_id` (FK) が存在する | 「ユーザー×キャラクター関係系」に分類されているため | ✅ **entities.md v3.1.8 に明示済み** |
| 11 | `payout_accounts` にデフォルト口座の部分UNIQUEが必要 | `is_default` + `deleted_at` でデフォルト口座を管理との記載から推測 | 仮定（要確認） |
| 12 | `conversation_sessions` に `user_id` と `character_id` (FK) が存在する | 「ユーザーとキャラクターの会話単位」との記載から推測 | ✅ **entities.md v3.1.8 に明示済み** |
| 13 | `conversation_messages` に `session_id` (FK) が存在する | 「会話内の個別発話」との記載から推測 | ✅ **entities.md v3.1.8 に明示済み** |

---

## 9. 未確定事項（質問）

### 9.1 ビジネスポリシーに関する質問

| # | 質問 | 影響範囲 |
|---|------|----------|
| 1 | **ユーザー削除は物理削除か論理削除か？** 会話ログ・購入履歴を残す方針か？ | `users` → 各テーブルの ON DELETE 設計 |
| 2 | **クリエイター退会時のキャラクター処理は？** 削除 / 運営に移管 / 公開停止（凍結）のどれか？ | `creators` → `characters` の ON DELETE 設計 |
| 3 | **購入済みPackの削除可否は？** 購入者の利用権はどう扱うか？ | `packs` の削除制約、`user_entitlements` の revoke 処理 |
| 4 | **会話ログの保持期間は？** 永続保持か、一定期間後に削除/アーカイブか？ | `conversation_messages` のパーティション設計 |

### 9.2 データモデルに関する質問

| # | 質問 | 影響範囲 |
|---|------|----------|
| 5 | **`audit_logs` は他テーブルへのFKを持つか？** 完全独立（イミュータブル）か？ | `audit_logs` の設計 |
| 6 | **`notifications` の宛先は `user_id` のみか？** クリエイター/運営向け通知は別か？ | `notifications` のFK設計 |
| 7 | **`events.event_type_id` は NOT NULL か NULL 許可か？** MVPでenum運用との記載あり | `events` → `m_event_types` のFK設計 |

---

## 改訂履歴

| バージョン | 日付 | 変更内容 | 担当者 |
|------------|------|----------|--------|
| 1.0.0 | 2026-01-31 | 初版作成（entities.md v3.1.7 を基に設計） | - |
| 1.0.1 | 2026-01-31 | クリティカル修正: DB前提明記、削除ポリシー暫定注記、packs物理削除の重要注意追加 | - |
| 1.0.2 | 2026-01-31 | 仮定一覧を更新: 11件の重要FK列が entities.md v3.1.8 に明示されたためステータス更新（character_personalities.character_id, reports/moderation_actions のFK含む）。2.9節の「※仮定」注記を削除 | - |

---

*本ドキュメントは entities.md v3.1.8 を基に作成したリレーションシップ設計です。「仮定」セクションで「仮定（要確認）」となっている項目は entities.md に明示されていないため、確認・修正が必要です。*
