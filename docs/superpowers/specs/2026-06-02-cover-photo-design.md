# 旅行カード カバー写真設計

**日付**: 2026-06-02  
**対象**: index.html（単一ページアプリ）

## 概要

各旅行カードにカバー写真を追加する。写真がない場合はtrip IDをハッシュして固定パレットから決めた単色を表示する。アップロードは旅行カードと旅行詳細の両方から行える。

## カードデザイン

### 写真あり
- カード上部に高さ110pxの写真エリアを全幅で表示
- `object-fit: cover` で中央クロップ
- 写真エリアをクリック → ファイル選択 → アップロード

### 写真なし（プレースホルダー）
- trip の `id` 文字列を単純ハッシュして以下8色のパレットから1色を決定
- 毎回同じ色が出る（ランダムではなく決定論的）

```js
var COVER_COLORS = [
  "#2d3e5a", // アクセント紺
  "#4a7c59", // グリーン
  "#7c4a6b", // パープル
  "#7c5a2d", // ブラウン
  "#2d6b7c", // ティール
  "#5a2d7c", // バイオレット
  "#7c2d2d", // レッド
  "#4a4a7c", // インディゴ
];
function getTripColor(id) {
  var hash = 0;
  for (var i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) & 0xffffffff;
  return COVER_COLORS[Math.abs(hash) % COVER_COLORS.length];
}
```

- プレースホルダー上に旅行名の頭文字（例: "W"）を薄く表示してもよい（任意）
- 写真エリアをクリック → ファイル選択 → アップロード（写真なし時もアップロード可）

## 旅行詳細ヘッダー（hero エリア）

- 現在の `.hero` エリアにカバー写真を背景として表示
- 写真あり: 背景画像 + 下からの暗いグラデーションオーバーレイ
- 写真なし: `getTripColor(trip.id)` の単色
- ヘッダー右上に 📷 ボタンを追加 → ファイル選択 → アップロード
- isViewOnly / isGuest 時は 📷 ボタンを非表示

## 画像処理（クライアント側）

アップロード前に以下の処理を行う:

1. ファイルサイズチェック: 5MB 超でトースト警告して中断
2. Canvas でリサイズ: 最大 1200×630px（アスペクト比維持）
3. JPEG 品質 0.8 で `toBlob()` → Blob として Firebase Storage にアップロード
4. 実際の保存サイズは概ね 100〜300KB

```js
async function resizeCoverImage(file) {
  return new Promise(function(resolve, reject) {
    if (file.size > 5 * 1024 * 1024) { toast("写真は5MB以内にしてください"); resolve(null); return; }
    var img = new Image();
    var url = URL.createObjectURL(file);
    img.onload = function() {
      var MAX_W = 1200, MAX_H = 630;
      var w = img.width, h = img.height;
      if (w > MAX_W) { h = Math.round(h * MAX_W / w); w = MAX_W; }
      if (h > MAX_H) { w = Math.round(w * MAX_H / h); h = MAX_H; }
      var canvas = document.createElement("canvas");
      canvas.width = w; canvas.height = h;
      canvas.getContext("2d").drawImage(img, 0, 0, w, h);
      URL.revokeObjectURL(url);
      canvas.toBlob(function(blob) { resolve(blob); }, "image/jpeg", 0.8);
    };
    img.onerror = function() { URL.revokeObjectURL(url); reject(new Error("画像読み込み失敗")); };
    img.src = url;
  });
}
```

## Firebase Storage / Firestore

- Storage パス: `users/{uid}/covers/{tripId}.jpg`
- アップロード後に `getDownloadURL()` で URL 取得
- `upd({coverUrl: url})` で Firestore の trip ドキュメントに保存
- 既存カバーを変更する場合も同じパスに上書きアップロードする（`{tripId}.jpg` で固定のため削除不要）

```js
async function uploadCoverPhoto(file) {
  if (isGuest) { toast("💡 保存するにはログインが必要です"); return; }
  var blob = await resizeCoverImage(file);
  if (!blob) return;
  var sel = getSel(); if (!sel) return;
  var path = "users/" + user.uid + "/covers/" + sel.id + ".jpg";
  var ref = storage.ref(path);
  await ref.put(blob, { contentType: "image/jpeg" });
  var url = await ref.getDownloadURL();
  await upd({ coverUrl: url });
  toast("カバー写真を設定しました");
}
```

## CSS 追加

```css
.trip-card-cover {
  width: 100%;
  height: 110px;
  object-fit: cover;
  display: block;
  border-radius: 16px 16px 0 0;
  cursor: pointer;
}
.trip-card-cover-placeholder {
  width: 100%;
  height: 110px;
  border-radius: 16px 16px 0 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: 900;
  color: rgba(255,255,255,0.25);
  letter-spacing: -1px;
}
/* カード本体はカバーがある時はtop paddingを0に */
.trip-card.has-cover { padding-top: 0; }
.trip-card.has-cover::before { display: none; } /* 左ボーダーバーを非表示 */
.hero-cover {
  width: 100%;
  height: 140px;
  object-fit: cover;
  display: block;
}
.hero-cover-placeholder {
  width: 100%;
  height: 140px;
}
```

## 変更関数

- `renderList()` → 各 trip-card に coverUrl があれば `<img class="trip-card-cover">` を、なければ `.trip-card-cover-placeholder` を挿入
- `renderDetail()` → `.hero` エリアにカバー写真または単色プレースホルダーを表示。📷 ボタン追加
- 新規追加: `resizeCoverImage(file)`, `uploadCoverPhoto(file)`, `getTripColor(id)`

## 非変更範囲

- Firebase Auth / Firestore の認証・データ構造（`coverUrl` フィールド追加のみ）
- 既存の添付ファイル機能
- スマホ・PC 両対応（既存レスポンシブそのまま）
- ゲストモードのデモデータ（DEMO_TRIPS に coverUrl なし → プレースホルダー表示）
