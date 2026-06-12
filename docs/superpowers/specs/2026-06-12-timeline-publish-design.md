# 旅行詳細から「投稿」できるようにする 設計

作成日: 2026-06-12

## 背景・目的

Tavy は単一の `index.html`（バニラ JS / Firestore / `ce`・`ap`・`tx` による手動 DOM 構築 + グローバル状態 + `render()`）で構成される旅行メモアプリ。

現状、旅行をタイムラインに公開する設定（公開するタブの選択・公開/更新/停止）は、ヘッダー右上の「共有」ボタンから開く `renderModal_share()` 内の「みんなのタイムラインに公開」セクションに埋め込まれている。リンク共有・メンバー招待と同じモーダルに混在しており、見つけにくい。

本変更で次を実現する。

1. 旅行詳細画面の「自分の旅行 / タイムライン」セグメントの右側に **「投稿」ボタン**を追加し、タイムライン公開を専用モーダルから行えるようにする。
2. **「編集」モーダルからもタイムライン公開設定を変更**できるようにする。
3. 絵文字は使わず、既存の `ICONS` / `svgIcon()` による SVG アイコンのみを使用する。

## 決定事項（ブレストの結論）

- 「投稿」ボタンは**専用の投稿モーダル**（`renderModal_publish`）を開く。
- 既存の「共有」モーダル内の「みんなのタイムラインに公開」セクションは**削除**し、共有モーダルはリンク共有・メンバー招待のみのシンプルな構成にする。
- 「投稿」ボタンは公開状態に応じて表示を切り替える：
  - 未公開：globe アイコン + 「投稿」
  - 公開中：check アイコン + 「公開中」
  - いずれもクリックで投稿モーダルを開く（管理も同モーダルで行う）。
- 編集モーダルでは、**一番下（保存ボタンの上）**にタイムライン公開セクションを配置する。
- 公開関連のアクション（投稿する／公開内容を更新する／公開を停止する）は、編集モーダル内でも**即時実行**（`upd`/`syncFeed`/`unpublishFeed` を直接呼び、トースト表示）とし、「保存する」ボタンの保存対象には含めない（既存の共有モーダルと同じ即時反映の挙動を維持）。
- 表示テキスト・アイコンに絵文字は使わない。「✓」などの記号も `svgIcon("check",...)` に置き換える。

## コンポーネント

### 1. `renderPublishSection(withHeading)`（新規・共通関数）

既存の「みんなのタイムラインに公開」ロジックを移植した共通パーツ。`getSel()` で対象旅行を取得し、`publishDraftTabs` を `sel.publicTabs`（無ければ `["itinerary"]`）から遅延初期化する。

- `withHeading=true` の場合、先頭に見出しラベル「タイムラインに公開」を表示（編集モーダル用）。`renderModal_publish` 側ではモーダルタイトルが同義のため `withHeading=false` で呼ぶ。
- `sel.publishedToFeed===true` の場合：
  - `svgIcon("check","var(--green)",...)` + 「タイムラインに公開中」（緑系テキスト）
  - `renderPublishTabPicker()`（既存のまま再利用）
  - 「公開内容を更新する」ボタン（`btn-ok`）→ `upd({publicTabs})` + `syncFeed()` + トースト
  - 「公開を停止する」ボタン（アウトライン）→ `unpublishFeed()` + `upd({publishedToFeed:false})` + トースト
- `sel.publishedToFeed!==true` の場合：
  - 説明文（既存文言を流用：「投稿すると、行程など選んだ内容がタイムラインに流れ、他のユーザーがいいね・コメントできます。」）
  - `renderPublishTabPicker()`
  - 「投稿する」ボタン（`btn-ok`）→ `ensureNickname()` 確認後、`upd({publishedToFeed:true,publicTabs})` + `syncFeed()` + `track('feed_publish',{})` + トースト「タイムラインに投稿しました！」
- いずれのボタン操作後も `publishDraftTabs=null` にリセットしてから `render()`（次回開いた時に最新の `sel.publicTabs` から再初期化させる）。

### 2. `renderModal_publish()`（新規）

- 状態: `showPublish`（bool、初期値 `false`）。
- タイトル: `svgIcon("globe","currentColor",18)` + 「タイムラインに投稿」
- 本文: `renderPublishSection(false)`
- フッター: 「閉じる」ボタン（`btn-cancel`）。
- 閉じる操作（オーバーレイクリック／閉じるボタン）で `showPublish=false; publishDraftTabs=null; render();`
- `render()` のモーダル分岐に `if(showPublish)ap(wrap,renderModal_publish());` を追加（`showShare` と同じ並び）。

### 3. 「投稿」/「公開中」ボタン（`renderListSeg` 拡張）

- `renderListSeg()` を `renderListSeg(trailing)` に拡張。`trailing` が渡された場合、セグメントの末尾（右側）に追加する。
- `renderList()`（トップページ）からの呼び出しは引数なし（変更なし）。
- `renderDetail()` では、`!isViewOnly && !isGuest && user && sel.ownerId===user.uid` の場合のみボタンを生成して渡す：
  - 未公開（`!sel.publishedToFeed`）: `svgIcon("globe","currentColor",14)` + 「投稿」、ニュートラル/アウトラインの見た目
  - 公開中（`sel.publishedToFeed`）: `svgIcon("check","var(--green)",14)` + 「公開中」、緑系の控えめな見た目
  - `onclick`: `publishDraftTabs=null; showPublish=true; render();`
- CSS: `.feed-seg` に `align-items:center` を追加。新規クラス `.feed-seg-post`（基本スタイル）と `.feed-seg-post.published`（緑系の配色）を追加し、`margin-left:auto` で右寄せする。

### 4. 編集モーダル (`renderModal_editTrip`) への追加

- 地域ピッカー（`renderRegionPicker`）の下、保存/キャンセルボタン行の上に `renderPublishSection(true)` を挿入。
- `openEditTrip()` の冒頭で `publishDraftTabs=null` をセットし、編集モーダルを開くたびに `sel.publicTabs` から再初期化させる。
- 編集モーダルのキャンセル／保存ハンドラでも `publishDraftTabs=null` をリセットする（次に共有/投稿/編集のどのモーダルを開いても状態が混ざらないようにする）。

### 5. 共有モーダル (`renderModal_share`) の整理

- 「みんなのタイムラインに公開」セクション（タブピッカー＋投稿/更新/停止ボタン群）を削除。
- 残るのは「リンクで共有（閲覧のみ）」と「メンバー招待」のセクションのみ。タイトル・全体構成は変更なし。

### 6. ガイド更新

ガイド画面（`guidePage==="guide"` のコンテンツ配列）に新しい項目を追加：

```js
{title:"タイムラインに投稿する",desc:"「自分の旅行」セグメントの右にある「投稿」ボタンから、公開したいタブを選んでタイムラインに投稿できます。編集画面からも公開設定（投稿・更新・停止）を変更できます。"}
```

挿入位置は「旅行を共有する」の前（投稿 → 共有 の順で説明する）。

## アイコン

すべて既存の `ICONS` を使用（追加不要）：

- `globe`（投稿ボタン・投稿モーダルタイトル）
- `check`（公開中ステータス表示・公開中ボタン）

## データフロー

- Firestore 上のフィールド（`publishedToFeed`, `publicTabs`, `feed` ドキュメント）は変更なし。既存の `upd()` / `syncFeed()` / `unpublishFeed()` / `ensureNickname()` / `track()` をそのまま再利用。
- `publishDraftTabs` はモーダル/セクションをまたいで共有されるグローバルなドラフト配列。各エントリポイント（投稿モーダルを開く・編集モーダルを開く・各操作完了後）で `null` にリセットし、`renderPublishSection` 内で遅延初期化することで常に最新の `sel.publicTabs` を反映する。

## 検証

プレビューでの手動確認:

1. オーナーで未公開 → 詳細画面のセグメント右に「投稿」ボタン（globe アイコン）が表示される。クリックで投稿モーダルが開き、タブピッカー＋「投稿する」が表示される。投稿後、同モーダル内が「公開中」表示に切り替わる。
2. オーナーで公開中 → セグメント右に「公開中」ボタン（check アイコン、緑系）。クリックで投稿モーダルが開き、「公開内容を更新する」「公開を停止する」が表示される。
3. 非オーナー／ゲスト／閲覧専用 → 「投稿」「公開中」ボタンは表示されない。
4. 編集モーダル → 一番下にタイムライン公開セクションが表示され、投稿/更新/停止が即時反映される（「保存する」とは独立）。
5. 共有モーダル → タイムライン公開セクションが無くなり、リンク共有・メンバー招待のみになっている。
6. 全体でコンソールエラーが出ないこと。絵文字が使われていないこと（テキスト・アイコンとも SVG/既存アイコンのみ）。

## スコープ外（YAGNI）

- `renderPublishTabPicker()` 自体のデザイン変更。
- Firestore スキーマ・セキュリティルールの変更。
- フィードカード（`renderFeedCard`）の表示変更。
- 新規 SVG アイコンの追加（既存の `globe` / `check` を再利用）。
