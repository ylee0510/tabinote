# 天気タブ 都市検索の場所特定（ディスアンビゲーション）設計

日付: 2026-06-10

## 背景・課題

天気タブで都市名を追加すると、`geocode()`（Nominatim, `limit=1`）が先頭1件だけを
採用するため、「Monterrey」と「モンテレイ」で別の地点になるなど、同名都市の取り違えが起きる。

ユーザー要望: 都市名を入力したら、場所を特定しやすい候補が現れて選べるようにしたい。

## 方針（承認済み）

- 入力するたびに候補表示（**デバウンス**で「打ち終わり」に1回だけ検索）
- ジオコーダーを **Open-Meteo Geocoding API** に切替（天気APIと同一提供元、
  Nominatimの「1秒1回・autocomplete非推奨」制約を回避、日本語ローカライズ済みで
  `admin1 / country / country_code` が構造化されて返る）

実測レイテンシ: 接続確立後 約0.3秒/件（サーバ処理は0.3ms、ほぼ通信往復）。

## 変更範囲

天気タブのみ。スポット（地図ピン）の `geocode()` は今回対象外。

## 詳細設計

### 1. ジオコーダー `geoSearch(q)`（新規）

```
GET https://geocoding-api.open-meteo.com/v1/search?name=<q>&count=6&language=ja
```

- 返り値: `[{name, admin1, country, country_code, lat, lng}, ...]`（結果なし/エラーは `[]`）
- クエリ単位でメモリキャッシュ（`geoCache[q]`）

### 2. 状態

- `weatherSuggestions`（現候補配列）
- `weatherSearchTm`（デバウンスタイマー）
- `geoCache`（クエリ→結果）

### 3. 入力UX（`renderWeather`）

- 入力欄の直下に候補コンテナ `<div id="weather-suggest">`
- `oninput`:
  1. `weatherCityInput` 更新
  2. 既存タイマーを `clearTimeout`
  3. trim長 < 2 → 候補コンテナを空にして終了
  4. それ以外 → 350ms後に `geoSearch` 実行
- 検索完了後: **`render()` を呼ばず**、`#weather-suggest` の中身を直接組み立てて
  差し替える（入力フォーカス維持のため）
- stale guard: 取得結果は、現在の入力値と検索クエリが一致する時のみ表示
- 候補行: `🇲🇽 モンテレイ`（主見出し）＋ 小さいグレーで `ヌエボ・レオン州, メキシコ`
  - onclick → 確定（下記 addWeatherCity）→ 入力欄と候補をクリア
- 候補0件: 「該当する都市が見つかりません」行を表示
- Enter / ＋ ボタン: 先頭候補があればそれを追加（フォールバック）

### 4. 確定処理 `addWeatherCity`（改修）

- 候補オブジェクトを受け取り、`weatherCities` に
  `{name, lat, lng, country, country_code, admin1}` を push
- 入力欄・候補・タイマーをリセット

### 5. データモデル（後方互換）

`weatherCities` 要素:

```
{ name, lat, lng, country?, country_code?, admin1? }
```

既存の `{name, lat, lng}` のみの項目も、国情報なしでそのまま表示できること。

### 6. 天気カード見出し

- `country` があれば `🏳 name, country`（例: `🇲🇽 モンテレイ, メキシコ`）
- なければ従来どおり `📍 name`
- 国旗は `country_code`（ISO-2）→ 地域インジケータ絵文字に変換

## エラー処理

- ネットワークエラー/タイムアウト → 候補は空（「該当なし」表示）、トーストは出さない
- 連打 → デバウンス＋stale guardで最後の入力のみ反映
- オフライン/旧データ → 国情報なしで描画

## 動作確認

- 「Monterrey」と入力 → メキシコ/コロンビア/スペイン等が候補に並ぶ
- 「モンテレイ」と入力 → 同じくメキシコ等が候補に並ぶ（同地点を選べる）
- 候補タップで正しい lat/lng のカードが追加され、見出しに国が出る
- 既存の登録済み都市が壊れず表示される
- 入力中にフォーカスが外れない
