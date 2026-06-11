# Tavy タイムライン機能 設計

**日付**: 2026-06-11
**対象**: index.html（単一ページアプリ）/ Firestore / セキュリティルール

## 概要

「公開してもいい」と選択した旅行が、専用の **タイムライン画面** に他ユーザーのカードとして流れてくる機能を追加する。各カードには **いいね** と **コメント** を付けられる。

公開は既存の共有リンク（`isPublic`）とは別の、より強い「不特定多数への公開」同意として扱い、専用フラグで制御する。公開する旅行は、メールアドレスや会員IDを含まない **公開用スナップショット** を `feed` コレクションに作って配信する。

## 決定事項（前提）

- **同意モデル**: 既存の `isPublic`（共有リンク）はそのまま。タイムライン掲載は新フラグ `publishedToFeed` で制御（別の同意レベル）。
- **権限**: タイムラインの閲覧は誰でも可（未ログイン含む）。いいね・コメントはログイン必須。
- **データ供給**: `trips` を直接公開せず、公開用スナップショット `feed` コレクションを作る。メール・会員IDは含めない。タップ時の詳細表示も feed スナップショットだけで完結し、`trips` 本体は読みに行かない。
- **公開タブ**: 行程（itinerary）は必須。その他のタブ（持ち物 / ToDo / スポット / 予算 / 天気）は公開時に選択可能。
- **カードデザイン**: 写真先行（インスタ風）。カバー画像は個人ページの旅行カードと同じ幅・高さ（横幅100% / 高さ110px / 角丸上16px）。画像なしは `getTripColor(tripId)` グラデ。
- **画面導線**: 一覧ページ上部のアンダーラインタブで「自分の旅行 / タイムライン」を切替（既存タブUIと統一）。
- **アイコン**: いいね（ハート）・コメント（吹き出し）は絵文字ではなく SVG（`svgIcon()` に追加）。

## 拡張性の原則：タブはレジストリ駆動

新規タブ（例: シンプルな「記録ノート」）を後から足しても、タイムライン機能側を変更せず対応できるようにする。そのため **タブ定義レジストリ** を1箇所に持ち、公開設定UI・スナップショット生成・閲覧表示のすべてがこのリストを回して動く構成にする。

```js
var TAB_DEFS = [
  {key:"itinerary", icon:"calendar", label:"行程", always:true}, // 常に公開・選択不可
  {key:"packing",   icon:"backpack", label:"持ち物"},
  {key:"todo",      icon:"check",    label:"ToDo"},
  {key:"places",    icon:"pin",      label:"スポット"},
  {key:"budget",    icon:"money",    label:"予算"},
  {key:"weather",   icon:"sun",      label:"天気"},
];
```

新規タブ追加時の作業は次の2点のみ。タイムライン機能側はノータッチ。

1. `TAB_DEFS` に1行追加
2. そのタブの描画関数を1つ用意（例: `renderNotes()`）— これは個人ページに新タブを足す時点でどのみち必要

補足: feed は公開時点のスナップショット（コピー）。既存の公開済み旅行に新タブを後付けした場合は、その旅行を再保存／再公開して再同期するまで反映されない。新規公開は問題なし。

## データ構造

### `trips` ドキュメント（既存に追加）

- `publishedToFeed`（boolean）— タイムライン掲載中フラグ
- `publicTabs`（string[]）— 公開タブのキー（`itinerary` は常に含む。例: `["itinerary","places","budget"]`）

### `feed` コレクション（新規・公開用スナップショット）

メール・会員IDは一切含めない。

```
feed/{tripId}
  ├ ownerId      (string)            投稿者UID（ルール判定用）
  ├ ownerName    (string)            表示名
  ├ ownerPhoto   (string|null)       アバター画像URL（任意）
  ├ name, destination, type          表示メタ
  ├ coverUrl     (string|null)
  ├ startDate, endDate
  ├ publicTabs   (string[])          公開タブ
  ├ content      (map)               選択タブの中身だけコピー { itinerary:[...], places:[...], ... }
  ├ publishedAt  (serverTimestamp)   並び順キー
  ├ likeCount    (number)
  ├ commentCount (number)
  ├ likes/{uid}      サブコレクション  重複防止のため uid をドキュメントIDに（中身は {createdAt} 程度）
  └ comments/{auto}  サブコレクション  { uid, name, text, createdAt }
```

## 公開フロー / 公開設定UI

既存の共有モーダル `renderModal_share()` 内に新セクション「みんなのタイムラインに公開」を追加する。

1. オーナーのみ表示（`sel.ownerId === user.uid`）
2. トグル「タイムラインに公開する」（`publishedToFeed`）
3. ON にすると公開タブのチェックリストを表示（`TAB_DEFS` を回す。`always:true` の行程はチェック済み＆無効でグレーアウト）
4. 「公開する／更新する」ボタン → `syncFeed(trip)`：選択タブの中身を集めて `feed/{tripId}` を作成・更新
5. OFF にすると `feed/{tripId}` を削除 → タイムラインから消える（`publishedToFeed=false`、`publicTabs` クリア）

### 自動再同期

公開中の旅行をオーナーが編集して保存したとき（既存 `upd()` の後）、`publishedToFeed === true` なら `syncFeed` を呼びスナップショットを更新する。`likeCount` / `commentCount` は同期で上書きせず、メタ情報と `content` のみマージ更新する。

### syncFeed の責務

- `trips` ドキュメントから公開メタと `publicTabs` 各タブの中身を抽出
- メール・会員ID等の非公開項目は除外
- `feed/{tripId}` に set（merge）。新規作成時のみ `likeCount=0`、`commentCount=0`、`publishedAt=serverTimestamp()` を初期化

## タイムライン画面 / カード

### 画面遷移

- 一覧ページ（`view==="list"`）上部にアンダーラインタブ「自分の旅行 / タイムライン」を追加
- 状態は `listMode`（`"mine"` / `"timeline"`）で管理

### フィード取得

- `feed` を `publishedAt` 降順で取得。v1 は `limit(30)` ＋「もっと見る」ボタンで追加読み込み（無限スクロールはしない）
- 未ログインでも閲覧可

### カード（写真先行A）

- カバー画像（横幅100% / 高さ110px / 角丸上16px。なければ `getTripColor(tripId)` グラデ。左上にタイプバッジ `🌏海外` 等）
- 投稿者行（アバター＝`ownerPhoto` か頭文字、`ownerName`、相対時刻「3日前」）
- タイトル（`name`）／メタ（`📍destination`・`startDate → endDate`）
- 公開タブのチップ列（`行程 スポット 予算` …）
- 区切り線の下にアクション行：いいね（SVGハート＋`likeCount`）／コメント（SVG吹き出し＋`commentCount`）

### カードのタップ挙動

- `feed/{tripId}` の `content` を読み込み、閲覧専用モード（`isViewOnly`）で詳細表示
- タブバーは `publicTabs` のみ描画
- 既存 `loadSharedTrip` と同系の経路を、`trips` 本体ではなく feed スナップショットから読む版として用意

## いいね

- カード／詳細どちらからもトグル可
- 未ログインなら「ログインするといいねできます」トースト
- `feed/{tripId}/likes/{uid}` を set/delete し、`likeCount` をトランザクションで増減
- 自分が押し済みかは `likes/{uid}` の存在で判定（SVGハートの塗り／線を出し分け）

## コメント

- 閲覧専用の詳細画面の下部に「コメント」セクション（一覧＋入力欄）
- 一覧: `feed/{tripId}/comments` を `createdAt` 昇順。各行に投稿者名・相対時刻・本文。自分の投稿には削除ボタン
- 投稿: ログイン必須（未ログインは入力欄の代わりに「ログインしてコメント」）。`{uid, name, text, createdAt}` を追加し `commentCount` を増加
- 削除: 自分のコメントのみ（`uid === user.uid`）。`commentCount` を減算
- 簡易ガード: 空文字禁止・最大文字数 500

## Firestore セキュリティルール

Firebase コンソール側でのルール更新が必須（コードのデプロイとは別作業として明記）。

- `feed/{id}`
  - read: 全員
  - create / delete: `request.auth.uid == resource.data.ownerId`（オーナーのみ）
  - update: オーナーは全項目可。ログイン済みユーザーは `likeCount` / `commentCount` の増減のみ許可
- `feed/{id}/likes/{uid}`
  - create / delete: `uid == request.auth.uid` のみ
- `feed/{id}/comments/{c}`
  - read: 全員
  - create: ログイン済み かつ `request.resource.data.uid == request.auth.uid`
  - delete: 本人（`resource.data.uid == request.auth.uid`）のみ

## SVG アイコン追加

`svgIcon()` のアイコンセットに以下を追加：

- `heart`（線 / 塗りの2状態で押下を表現）
- `comment`（吹き出し）

## スコープ外（v1 では実装しない / YAGNI）

- 通報・ブロック・モデレーション
- ハッシュタグ / 検索 / フォロー
- コメントへの返信スレッド・コメントへのいいね
- 無限スクロール（v1 は「もっと見る」ボタン）
- 通知

## 変更範囲まとめ

### HTML / CSS（index.html）

- タイムラインカード・アンダーライン切替タブ・コメントセクションのスタイル追加
- 共有モーダルに公開設定セクションのスタイル追加

### JavaScript（index.html）

- `TAB_DEFS` レジストリ導入と既存タブ描画の寄せ替え
- `publishedToFeed` / `publicTabs` の状態と公開設定UI
- `syncFeed` / 公開停止 / `upd()` 後の自動再同期
- `listMode` とタイムライン一覧描画 / フィード取得・ページング
- feed スナップショットからの閲覧専用詳細表示
- いいね（トグル・カウンタ・トランザクション）
- コメント（一覧・投稿・削除・カウンタ）
- `svgIcon()` に `heart` / `comment` 追加

### Firestore（コンソール作業）

- `feed` コレクションのセキュリティルール追加

## 非変更範囲

- 既存の `isPublic` 共有リンク機能
- Firebase 認証・既存のデータ連携ロジック
- スマホ / レスポンシブの既存挙動
