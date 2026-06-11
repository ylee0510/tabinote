# 旅行カードの編集・地域タグ付け・絞り込み 設計

作成日: 2026-06-11

## 背景・目的

Tavy は単一の `index.html`（バニラ JS / Firestore / `ce`・`ap`・`tx` による手動 DOM 構築 + グローバル状態 + `render()`）で構成される旅行メモアプリ。現状、旅行の `destination` は自由入力テキストのみで、作成後に旅行名・目的地を編集する UI が無い。トップページ（「自分の旅行」「タイムライン」）に地域での絞り込みも無い。

本変更で次の 3 つを実現する。

1. 旅行カードの **タイトル・目的地などを編集**できるようにする。
2. **作成時に地域を複数選択**で付与する（海外＝国、国内＝都道府県）。大陸/地方でグルーピングし、その中に国/県を折りたためるアコーディオン形式。
3. トップページから **国/都道府県で絞り込み**できるようにする（「自分の旅行」「タイムライン」両方）。

## 決定事項（ブレストの結論）

- 目的地は **構造化 `regions` と自由入力 `destination` の両方を保持**する。
- トップページの操作は **絞り込み（フィルタ）**。並べ替えは行わない。
- タイムラインの絞り込みは **Firestore 再クエリ**（`regions` array-contains）で全件を正しく拾う。
- 編集可能な項目は **旅行名 / 目的地（自由入力）/ regions / 出発日・帰着日**（全項目）。種類トグルも編集モーダルに置く（地域ピッカーの国/県切替に必要なため）。
- 国リストは **大陸で分類し、配下に国を折りたたむ**形式（世界を網羅）。

## データモデル

### `trips` ドキュメント（追加フィールド）

- `regions: string[]` — 正規化した日本語名を直接格納。
  - 海外（`type==="overseas"`）: 国名の配列（例 `["韓国","台湾"]`）。
  - 国内（`type==="domestic"`）: 都道府県名の配列（例 `["東京都","京都府"]`）。
  - `type` と整合させる。海外⇄国内を切り替えたら `regions` はクリアする。
  - 既存旅行は `regions` 未設定（`undefined`）のまま。編集モーダルで後から付与できる。フィルタ・表示では空配列として扱う。
- `destination: string` — 既存の自由入力テキスト。都市名など細かい情報用。変更なし。

### `feed` ドキュメント（追加フィールド）

- `regions: string[]` — `syncFeed()` で trip からミラーする。タイムラインの再クエリに使用。

## 静的マスタ（JS const として追加）

### `COUNTRIES_BY_CONTINENT`

大陸見出し → 国の配列（`{name, cc}`、`cc` は ISO2、`flagEmoji(cc)` で国旗表示）。世界を網羅。大陸グループ:

- アジア
- ヨーロッパ
- 北米・カリブ海地域（米・加・カリブ諸島）
- 中南米（メキシコ・中米・南米）
- オセアニア
- 中東
- アフリカ

### `PREFS_BY_REGION`

地方見出し → 都道府県名の配列。47 都道府県を網羅:

- 北海道・東北
- 関東
- 中部
- 近畿
- 中国
- 四国
- 九州・沖縄

### ルックアップ

`regions` の各文字列から所属グループ（大陸/地方）と `cc` を引けるよう、マスタから派生インデックス（name → {group, cc}）を一度構築しておく。フィルタ用 optgroup 構築・国旗表示に使う。

## コンポーネント

### 1. 地域ピッカー（作成・編集モーダル共通の新規部品）

`renderRegionPicker(mode, selected, onChange)` 相当。

- `mode`（`overseas` / `domestic`）に応じて `COUNTRIES_BY_CONTINENT` か `PREFS_BY_REGION` を表示。
- **選択済みチップ**: ピッカー上部に削除可能なチップ列で表示。
- **アコーディオン**: 大陸/地方の見出し行をタップで開閉。配下に各地域のトグルチップ（選択状態を反映）。
- 選択変更は呼び出し元の state（`tripForm.regions` または編集ドラフト）を更新して `render()`。

### 2. 作成モーダル `renderModal_newTrip`（既存を拡張）

- 種類トグルの下に地域ピッカーを追加。
- `tripForm` に `regions: []` を追加。種類トグル切替時に `regions` をクリア。
- `createTrip()` で `regions: tripForm.regions` を保存。作成後の `tripForm` リセットにも `regions:[]` を含める。

### 3. 編集モーダル `renderModal_editTrip`（新規）

- 状態: `showEditTrip`（bool）+ `editDraft`（編集対象のコピー: `{name, destination, startDate, endDate, type, regions}`）。
- 構成: 種類トグル（切替時は確認の上 `regions` クリア）/ 旅行名 / 目的地（自由入力）/ 出発日・帰着日 / 地域ピッカー。
- 保存は既存 `upd(patch)` で `{name, destination, startDate, endDate, type, regions}` を更新。
- エントリポイント: **詳細画面ヒーロー部に「編集」ボタン**を追加（オーナーのみ、`!isViewOnly && !isGuest && sel.ownerId===user.uid`）。

### 4. トップページの地域フィルタ

セグメント（「自分の旅行」「タイムライン」）の下にグループ化した `<select>`（optgroup）を配置。既定は「すべての地域」。

- 状態: `mineRegionFilter`（既定 `""`）, `tlRegionFilter`（既定 `""`）。
- **自分の旅行**: クライアント側で `trips` を選択地域でフィルタ（`regions.includes(filter)`）。select の選択肢は、現在の `trips` が持つ `regions` を集計し、所属グループで optgroup 化して生成（存在する地域のみ）。
- **タイムライン**: 選択変更時に feed を再クエリ。
  - フィルタ無し: 既存どおり `feed.orderBy("publishedAt","desc").limit(30)`。
  - フィルタ有り: `feed.where("regions","array-contains",地域).orderBy("publishedAt","desc").limit(30)`。
  - 切替時に `feedItems=[]; feedLastDoc=null; feedDone=false;` でページングをリセットして再取得（`loadFeed` を地域引数対応に拡張）。
  - select の選択肢は静的マスタ全件（大陸＋地方の optgroup を 1 つの select にまとめる）。

### 5. カード／詳細表示

- 旅行カード（`renderList` 内）と詳細ヒーロー（`renderDetail`）、フィードカード（`renderFeedCard`）に `regions` のチップ/ラベルを表示（国旗 + 名前）。`destination` テキストは従来どおり併記。
- `regions` が空なら従来表示（`destination` のみ）。

## Firestore

- `syncFeed()` に `regions: trip.regions || []` を追加。
- **複合インデックス**: `feed` コレクションに `regions`(ARRAY_CONTAINS) + `publishedAt`(DESC) の複合インデックスを作成。`docs/firestore-feed-rules.md` に追記。
- セキュリティルール: `regions` は `trips` / `feed` の通常フィールドとしてオーナー書込みで通る想定（既存ルールで追加変更が不要か確認する）。

## 検証

テスト基盤の無い単一 HTML のため、preview による手動フロー確認を行う:

1. 新規作成（海外）で国を複数選択 → カード・詳細に regions 表示。
2. 新規作成（国内）で都道府県を複数選択 → 表示確認。
3. 既存旅行を編集 → 旅行名・目的地・日付・regions を変更 → 反映確認。
4. 種類トグル切替で regions がクリアされること。
5. 「自分の旅行」で地域フィルタ → 該当のみ表示、解除で全件。
6. 「タイムライン」で地域フィルタ → Firestore 再クエリで該当公開旅行が出る、「もっと見る」も同フィルタ。

## スコープ外（YAGNI）

- 並べ替え（ソート順変更）。今回は絞り込みのみ。
- 複数地域の AND 絞り込み。単一地域の絞り込みのみ。
- 地域マスタの管理画面・多言語化。
