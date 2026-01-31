# AI will 機能一覧

> **生成日:** 2026-01-31  
> **ソース:** user_stories_end_user.md, prioritization_end_user.md, チャット内設計議論

---

## 優先順位定義

| 優先度 | 定義 |
|--------|------|
| **Must** | MVP必須。これがないとサービスが成立しない / ストア審査に通らない |
| **Should** | 初期リリース後すぐに必要。収益化・リテンション・サポート負荷軽減に直結 |
| **Could** | あると良いがリソース次第で後回し可能。差別化・UX高度化 |

---

## ロール定義

| ロール | 定義 |
|--------|------|
| **EndUser** | エンドユーザーが直接操作・体験する機能（UI/画面） |
| **System** | 基盤・認証・ガード・APIなど、UIを介さずシステムが処理する機能 |
| **Ops** | 運用・初期データ投入など、サービス運営側が実行する機能 |

---

## 機能ID採番ルール

- 形式: `F-<CAT>-###`
- CAT: XCT(Cross-cutting), AUTH, AGE, MKT, CONV, SAFE, PRIV, COMM, MEM
- ###: カテゴリ内連番（001〜）

---

## Cross-cutting

| 機能ID | 機能名 | カテゴリ | 優先順位 | ロール |
|--------|--------|----------|----------|--------|
| F-XCT-001 | APIエラーレスポンス標準化 | Cross-cutting | Must | System |
| F-XCT-002 | 全般エラーハンドリング（ネットワーク/サーバー/認証失敗等） | Cross-cutting | Must | EndUser |
| F-XCT-003 | ローディング状態表示 | Cross-cutting | Must | EndUser |
| F-XCT-004 | 認証ミドルウェア（トークン検証/ユーザー特定） | Cross-cutting | Must | System |
| F-XCT-005 | ガード例外ルール（consent/age whitelist） | Cross-cutting | Must | System |
| F-XCT-006 | ユーザーステータス取得API（/me） | Cross-cutting | Must | System |
| F-XCT-007 | ログイン状態管理（未認証時リダイレクト） | Cross-cutting | Must | EndUser |
| F-XCT-008 | オンボーディング状態管理（未同意/未年齢のリダイレクト） | Cross-cutting | Must | EndUser |
| F-XCT-009 | 設定画面（基本） | Cross-cutting | Must | EndUser |
| F-XCT-010 | MVP用Persona/Scenario同梱（最低1件） | Cross-cutting | Must | Ops |
| F-XCT-011 | アクセスログ/監査ログ (Phase3) | Cross-cutting | Could | System |

> **Note:**  
> - F-XCT-002「全般エラーハンドリング」は登録/認証失敗時のエラー表示・再試行UIを含む（重複統合済み）  
> - F-XCT-005「ガード例外ルール」は、同意保存API・年齢保存APIをガード適用外とするルール（実装事故防止）  
> - F-XCT-010 は non-story engineering task だが、空一覧だと会話体験が成立しないためMust

---

## Onboarding/Auth

| 機能ID | 機能名 | カテゴリ | 優先順位 | ロール |
|--------|--------|----------|----------|--------|
| F-AUTH-001 | ユーザー登録API | Onboarding/Auth | Must | System |
| F-AUTH-002 | セッション管理/認証トークン発行 | Onboarding/Auth | Must | System |
| F-AUTH-003 | 利用規約/プライバシーポリシー同意保存API | Onboarding/Auth | Must | System |
| F-AUTH-004 | 同意ガード（未同意は保護API拒否） | Onboarding/Auth | Must | System |
| F-AUTH-005 | メール+パスワード登録フォーム | Onboarding/Auth | Must | EndUser |
| F-AUTH-006 | 利用規約・プライバシーポリシー同意UI | Onboarding/Auth | Must | EndUser |
| F-AUTH-007 | 登録完了→年齢確認遷移 | Onboarding/Auth | Must | EndUser |
| F-AUTH-008 | メール/パスワードログイン画面 | Onboarding/Auth | Must | EndUser |
| F-AUTH-009 | メール確認リンク送信 (Phase2) | Onboarding/Auth | Should | System |
| F-AUTH-010 | メール認証完了処理 (Phase2) | Onboarding/Auth | Should | System |
| F-AUTH-011 | パスワードリセット要求フォーム (Phase2) | Onboarding/Auth | Should | EndUser |
| F-AUTH-012 | パスワードリセットメール送信 (Phase2) | Onboarding/Auth | Should | System |
| F-AUTH-013 | パスワード再設定画面 (Phase2) | Onboarding/Auth | Should | EndUser |
| F-AUTH-014 | ソーシャルログイン（Google/Apple/LINE） (Phase3) | Onboarding/Auth | Could | EndUser |

---

## Age/Compliance

| 機能ID | 機能名 | カテゴリ | 優先順位 | ロール |
|--------|--------|----------|----------|--------|
| F-AGE-001 | 年齢情報保存API | Age/Compliance | Must | System |
| F-AGE-002 | 年齢ガード（未完了は保護API拒否） | Age/Compliance | Must | System |
| F-AGE-003 | 年齢に基づくコンテンツ制限ロジック | Age/Compliance | Must | System |
| F-AGE-004 | 年齢確認入力画面（生年月日/年齢帯） | Age/Compliance | Must | EndUser |
| F-AGE-005 | 年齢未確認時の利用制限UI | Age/Compliance | Must | EndUser |
| F-AGE-006 | 年齢変更不可説明・サポート案内 | Age/Compliance | Must | EndUser |
| F-AGE-007 | 未成年の課金上限制限 (Phase2) | Age/Compliance | Should | System |

---

## Marketplace Discovery

| 機能ID | 機能名 | カテゴリ | 優先順位 | ロール |
|--------|--------|----------|----------|--------|
| F-MKT-001 | Persona/Scenario一覧取得API | Marketplace Discovery | Must | System |
| F-MKT-002 | Persona/Scenario一覧画面 | Marketplace Discovery | Must | EndUser |
| F-MKT-003 | 詳細情報取得API | Marketplace Discovery | Must | System |
| F-MKT-004 | 詳細ページ（説明/価格/評価/レビュー件数） | Marketplace Discovery | Must | EndUser |
| F-MKT-005 | キーワード検索（名前/説明/タグ） (Phase2) | Marketplace Discovery | Should | EndUser |
| F-MKT-006 | 所持済み/未所持/無料ステータス表示 (Phase2) | Marketplace Discovery | Should | EndUser |
| F-MKT-007 | 評価/レビュー件数の実データ表示 (Phase2) | Marketplace Discovery | Should | EndUser |
| F-MKT-008 | フィルタUI（性格/価格帯/レーティング/タグ） (Phase3) | Marketplace Discovery | Could | EndUser |
| F-MKT-009 | フィルタ対応API (Phase3) | Marketplace Discovery | Could | System |
| F-MKT-010 | ソート切替（人気/新着/評価/価格） (Phase3) | Marketplace Discovery | Could | EndUser |
| F-MKT-011 | サンプル再生（テキスト/ボイス） (Phase3) | Marketplace Discovery | Could | EndUser |

> **Note:**  
> - F-MKT-004「詳細ページ」はPhase1では評価/レビュー件数を固定値(0)表示でも可。実データ表示・投稿機能はPhase2以降（F-MKT-007）

---

## Conversation

> **スコープ:** Text / Voice / Threads

| 機能ID | 機能名 | カテゴリ | 優先順位 | ロール |
|--------|--------|----------|----------|--------|
| F-CONV-001 | テキストメッセージ送信API | Conversation | Must | System |
| F-CONV-002 | 会話スレッド保存 | Conversation | Must | System |
| F-CONV-003 | 会話履歴取得API | Conversation | Must | System |
| F-CONV-004 | Persona/Scenario選択→会話画面遷移 | Conversation | Must | EndUser |
| F-CONV-005 | テキスト入力・送信UI | Conversation | Must | EndUser |
| F-CONV-006 | 会話履歴表示 | Conversation | Must | EndUser |
| F-CONV-007 | 応答遅延/タイムアウト時エラー表示 | Conversation | Must | EndUser |
| F-CONV-008 | 応答再試行導線 | Conversation | Must | EndUser |
| F-CONV-009 | 複数会話スレッド一覧画面 (Phase2) | Conversation | Should | EndUser |
| F-CONV-010 | スレッド切り替え・再開UI (Phase2) | Conversation | Should | EndUser |
| F-CONV-011 | スレッド一覧取得API (Phase2) | Conversation | Should | System |
| F-CONV-012 | 音声モード切替UI (Phase3) | Conversation | Could | EndUser |
| F-CONV-013 | マイク権限要求・許可導線 (Phase3) | Conversation | Could | EndUser |
| F-CONV-014 | 音声入力処理（STT連携） (Phase3) | Conversation | Could | System |
| F-CONV-015 | 音声出力処理（TTS連携） (Phase3) | Conversation | Could | System |

---

## Safety

> **スコープ:** Report / Block

| 機能ID | 機能名 | カテゴリ | 優先順位 | ロール |
|--------|--------|----------|----------|--------|
| F-SAFE-001 | 通報登録API | Safety | Must | System |
| F-SAFE-002 | 通報理由選択UI | Safety | Must | EndUser |
| F-SAFE-003 | 通報受付完了表示 | Safety | Must | EndUser |
| F-SAFE-004 | 通報開始導線（AI発言/Persona/Scenario） | Safety | Must | EndUser |
| F-SAFE-005 | 通報任意コメント入力 (Phase2) | Safety | Should | EndUser |
| F-SAFE-006 | 重複通報抑制 (Phase2) | Safety | Should | System |
| F-SAFE-007 | ブロック機能UI（クリエイター/コンテンツ/タグ） (Phase2) | Safety | Should | EndUser |
| F-SAFE-008 | ブロック登録/解除API (Phase2) | Safety | Should | System |
| F-SAFE-009 | ブロック対象の非表示（検索/おすすめ） (Phase2) | Safety | Should | System |
| F-SAFE-010 | レビュー通報導線 (Phase2) | Safety | Should | EndUser |

> **Note:**  
> - F-SAFE-004「通報開始導線」はPhase1ではレビュー対象を含めない。レビュー通報はPhase2以降（F-SAFE-010）

---

## Privacy

> **スコープ:** Delete / Export

| 機能ID | 機能名 | カテゴリ | 優先順位 | ロール |
|--------|--------|----------|----------|--------|
| F-PRIV-001 | 設定画面に削除導線 | Privacy | Must | EndUser |
| F-PRIV-002 | 会話履歴削除API | Privacy | Must | System |
| F-PRIV-003 | 会話履歴削除UI | Privacy | Must | EndUser |
| F-PRIV-004 | Personaごと等の単位削除UI (Phase2) | Privacy | Should | EndUser |
| F-PRIV-005 | 単位別削除API (Phase2) | Privacy | Should | System |
| F-PRIV-006 | 全データ削除時の猶予/注意事項表示 (Phase2) | Privacy | Should | EndUser |
| F-PRIV-007 | エクスポート要求UI (Phase3) | Privacy | Could | EndUser |
| F-PRIV-008 | エクスポート要求API (Phase3) | Privacy | Could | System |
| F-PRIV-009 | エクスポートデータ範囲明記 (Phase3) | Privacy | Could | EndUser |
| F-PRIV-010 | エクスポートダウンロード導線 (Phase3) | Privacy | Could | EndUser |
| F-PRIV-011 | エクスポートステータス管理（受付/準備中/完了/失敗） (Phase3) | Privacy | Could | System |

> **Note:**  
> - F-PRIV-007〜011のエクスポート機能は設定画面（F-PRIV-001）から遷移

---

## Commerce

> **スコープ:** Purchase / Restore

| 機能ID | 機能名 | カテゴリ | 優先順位 | ロール |
|--------|--------|----------|----------|--------|
| F-COMM-001 | 購入開始ボタン（詳細ページ） (Phase2) | Commerce | Should | EndUser |
| F-COMM-002 | 購入確認画面（価格/内容/支払い方法） (Phase2) | Commerce | Should | EndUser |
| F-COMM-003 | 購入処理API（レシート検証/付与） (Phase2) | Commerce | Should | System |
| F-COMM-004 | 購入完了→マイライブラリ追加 (Phase2) | Commerce | Should | EndUser |
| F-COMM-005 | 購入失敗/キャンセル時エラー表示・再試行 (Phase2) | Commerce | Should | EndUser |
| F-COMM-006 | 購入復元（Restore purchases）UI (Phase2) | Commerce | Should | EndUser |
| F-COMM-007 | 購入復元API (Phase2) | Commerce | Should | System |
| F-COMM-008 | 二重購入防止（所持済みチェック） (Phase2) | Commerce | Should | System |

---

## Memory

> **スコープ:** Clips

| 機能ID | 機能名 | カテゴリ | 優先順位 | ロール |
|--------|--------|----------|----------|--------|
| F-MEM-001 | メッセージ選択→メモリー保存UI (Phase2) | Memory | Should | EndUser |
| F-MEM-002 | メモリー保存API (Phase2) | Memory | Should | System |
| F-MEM-003 | メモリー一覧画面 (Phase2) | Memory | Should | EndUser |
| F-MEM-004 | メモリー一覧取得API (Phase2) | Memory | Should | System |
| F-MEM-005 | メモリー削除（確認ダイアログ付き） (Phase2) | Memory | Should | EndUser |
| F-MEM-006 | メモリー削除API (Phase2) | Memory | Should | System |
| F-MEM-007 | メタ情報付与UI（タイトル/タグ/フォルダ） (Phase3) | Memory | Could | EndUser |
| F-MEM-008 | メモリー検索・並び替えUI (Phase3) | Memory | Could | EndUser |
| F-MEM-009 | 紐づき情報表示（Persona/Scenario） (Phase3) | Memory | Could | EndUser |
| F-MEM-010 | ゴミ箱保持・復元機能 (Phase3) | Memory | Could | System |

---

## サマリー

| 優先度 | 機能数 |
|--------|--------|
| **Must** | 44 |
| **Should** | 35 |
| **Could** | 19 |
| **合計** | **98** |

### Must Top 10（優先実装順）

| 順位 | 機能ID | 機能名 | 理由 |
|------|--------|--------|------|
| 1 | F-XCT-001 | APIエラーレスポンス標準化 | 全APIの基盤。最初に設計・実装すべき |
| 2 | F-AUTH-001 | ユーザー登録API | サービス開始の入口 |
| 3 | F-XCT-004 | 認証ミドルウェア | 全保護APIの前提。セキュリティの根幹 |
| 4 | F-AUTH-002 | セッション管理/認証トークン発行 | ログイン維持の前提 |
| 5 | F-XCT-005 | ガード例外ルール | 実装事故防止。ガードが保存APIをブロックしないルール |
| 6 | F-AUTH-003 | 同意保存API | 法的要件。ガード例外対象 |
| 7 | F-AUTH-004 | 同意ガード | UI回避対策。サーバ側ブロック必須 |
| 8 | F-AGE-001 | 年齢保存API | ストア審査要件。ガード例外対象 |
| 9 | F-AGE-002 | 年齢ガード | UI回避対策。サーバ側ブロック必須 |
| 10 | F-XCT-006 | ユーザーステータス取得API(/me) | 状態管理UIの前提。オンボーディング制御に必須 |

---

## 変更履歴

| 日付 | 変更内容 |
|------|----------|
| 2026-01-31 | 初版作成。チャット内設計議論に基づきv2統合版を反映 |
| 2026-01-31 | v1.1: セクション見出し統一（Memory含む）、ロール定義整合（F-XCT-002/007/008をEndUserに）、F-PRIV-001名称修正 |

