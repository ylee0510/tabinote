# メモタブ「AIモード」機能 設計書

## 概要

メモタブ（`renderNote`）に「AIモード」を追加する。ログイン済みユーザーは、AIモードを開くことで以下の2つの方法で旅行先に関する情報をAIに生成させ、メモ欄に追加できる。

1. **テーマ提案**: 「歴史」「言語・あいさつ」など複数のテーマを選択し、「AIで提案」を押すと、選択したテーマごとに見出し付きの文章がメモ欄に追加される。
2. **自由記述（チャット風）**: 「〇〇について教えて」のように自由入力すると、その回答が見出し付きでメモ欄に追加される。

AI呼び出しは開発者負担のAPI（Gemini）を使うため、利用者は **ログイン済みユーザーのみ**（ゲストモード除外）。閲覧専用リンク（`isViewOnly`）では元々メモ編集UI自体が表示されないため対象外。

## 背景: 現在のメモタブ実装

- `sel.note` は文字列配列（`noteList(sel)`で正規化）
- `renderNote(sel)`:
  - `isViewOnly`時は読み取り専用表示のみ
  - それ以外: ヒント文 → 各メモを`<textarea class="note-ta">`として表示（空欄含め`noteExtraBoxes`分余分に表示）→ 「＋ 追加」ボタン
  - `onblur`で全textareaの値を集めて`upd({note: vals})`で保存。末尾の空文字列は除去。

## UI/UXデザイン

### 配置とトグル

ヒント文（`.note-hint`）の直後に「AIモード」トグルボタンを追加する。`sparkles`アイコン（新規SVG）＋テキスト「AIモード」。状態は`showAiMode`（boolean、初期値`false`）。

表示条件: `!isGuest && user`（ログイン済みユーザーのみ。ゲストには表示しない）。

### AIパネル（`showAiMode===true`のとき表示）

1. **テーマ選択チップ**: `AI_THEME_DEFS`（8件、後述）をトグル可能なチップ/ピルボタンとして横並び表示（複数選択可）。選択状態は`aiThemes`（選択中のkey配列）。選択中チップは強調表示（既存の`.rp-chip`的なアクセントカラー塗り、未選択は枠線のみ）。

2. **「AIで提案」ボタン**: `aiThemes`が1件以上選択されている場合のみ有効。押すと選択テーマ分を一括でAPIに問い合わせ、結果をテーマごとに見出し付きメモとして追加する。

3. **自由記述欄**: `<input type="text" class="finp" maxlength="200">`＋「聞く」ボタン。状態は`aiQuestion`。空文字のときはボタン無効化。押すとAPIに問い合わせ、結果を見出し付きメモとして追加する。`maxlength="200"`で入力量を制限する（コスト・乱用対策）。

4. **ローディング表示**: API呼び出し中は`aiLoading=true`。「AIで提案」「聞く」両ボタンを無効化し、押されたボタンのラベルを「生成中...」に変更する。

### 生成結果の挿入

既存の`note`配列の末尾に追加し、`noteExtraBoxes=0`にしてから`upd({note: vals})`で保存（既存の追加・削除パターンと同様）。

- テーマ提案: 選択した各テーマについて1件ずつ追加。形式:
  ```
  【<テーマラベル>】(AI生成)
  <本文>
  ```
- 自由記述: 1件追加。形式:
  ```
  【AIへの質問: <質問文>】(AI生成)
  <回答>
  ```

生成成功後、`aiThemes=[]`にリセット（同じテーマを連続生成してしまうのを防ぐ）。自由記述は`aiQuestion=""`にリセット。`showAiMode`は開いたままにする（連続して使えるように）。

### テーマ定義一覧（`AI_THEME_DEFS`）

| key | ラベル（チップ表示・見出しに使用） | AIへの指示内容（プロンプトの一部） |
|---|---|---|
| history | 歴史 | その土地の歴史的背景・史跡 |
| language | 言語・あいさつ | 現地で使われている言語、簡単なあいさつ・言い回し |
| shops | おすすめのお店・グルメ | 具体的な店名を含むおすすめのレストラン・ショップ |
| spots | おすすめのスポット | 定番から少し外れた訪れる価値のある場所 |
| transport | 交通・移動 | 電車・バス・タクシー事情、ICカードなど |
| safety | 治安・物価・注意事項 | 治安状況、物価感（食事・交通などの目安）、旅行者が気をつけるべき点 |
| food_culture | 食事・グルメ事情 | 食文化、チップ習慣、食事マナーなど（おすすめのお店とは別観点） |
| events | イベント・祭り | 旅行期間に合った現地のイベント・祭り |

## 新規状態変数

```javascript
var showAiMode=false;   // AIパネルの開閉
var aiThemes=[];        // 選択中のテーマキー配列
var aiQuestion="";       // 自由記述の入力値
var aiLoading=false;     // 生成中フラグ
```

リセットタイミング: 新規追加の状態であり、デフォルト値のままでもアプリ全体の動作に影響しないため、トリップ切り替え時の明示的リセットは行わない（YAGNI）。ただし生成成功時は上記の通り`aiThemes`/`aiQuestion`をリセットする。

## 新規アイコン

`ICONS`に`sparkles`を追加（AIモードのトグルボタンに使用）。絵文字は使わずSVGパスで表現する。

## バックエンド: Netlify Function

### ファイル

- `netlify/functions/ai-memo.js` — メイン処理
- `netlify/functions/package.json` — `firebase-admin`を依存に追加
- `netlify.toml` — functionsディレクトリ設定を追加

### エンドポイント

クライアントから`POST /.netlify/functions/ai-memo`にリクエストする（Netlify Functionsのデフォルトパス規則）。

### 認証

クライアントは`user.getIdToken()`で取得したFirebase IDトークンを`Authorization: Bearer <token>`ヘッダーで送信。Function側は`firebase-admin`の`verifyIdToken`で検証。検証失敗時は`401`を返す。

### リクエスト/レスポンス契約

**テーマ提案モード**

リクエスト:
```json
{
  "mode": "themes",
  "destination": "京都・大阪",
  "regions": ["京都府", "大阪府"],
  "type": "domestic",
  "startDate": "2026-07-01",
  "endDate": "2026-07-05",
  "themes": ["history", "shops"]
}
```

レスポンス:
```json
{
  "results": [
    {"theme": "history", "text": "..."},
    {"theme": "shops", "text": "..."}
  ]
}
```

**自由記述モード**

リクエスト:
```json
{
  "mode": "question",
  "destination": "京都・大阪",
  "regions": ["京都府", "大阪府"],
  "type": "domestic",
  "startDate": "2026-07-01",
  "endDate": "2026-07-05",
  "question": "子連れでも楽しめるスポットは？"
}
```

レスポンス:
```json
{"answer": "..."}
```

**エラー時（両モード共通）**

```json
{"error": "エラーメッセージ"}
```

クライアントはこの場合およびネットワークエラー時、toast「AI生成に失敗しました。しばらくしてから再度お試しください。」を表示し、`aiLoading=false`に戻す（`finally`で必ず実行）。

### Gemini API呼び出し

Gemini本体の呼び出しは追加のnpmパッケージを使わず、Node.jsの`fetch`でREST API（`https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`）を直接呼び出す。`netlify/functions/package.json`の依存は`firebase-admin`のみ。

- モデル: `gemini-2.5-flash`（環境変数`GEMINI_API_KEY`、`GEMINI_MODEL`で上書き可能、デフォルト`gemini-2.5-flash`）
- テーマ提案モード: 選択された全テーマを1回のAPI呼び出しでまとめて問い合わせる（コスト削減のため）。`responseMimeType: "application/json"`を指定し、`{"results":[{"theme":"...","text":"..."}]}`形式での返却を指示。
- 自由記述モード: プレーンテキストで回答を取得。
- `maxOutputTokens`を設定し、出力量を制限（テーマ提案: テーマ数 × 300トークン程度を目安に動的設定、自由記述: 500トークン程度）。
- プロンプトには以下を含める: 旅行先（`destination`/`regions`）、旅行種別（海外/国内）、旅行期間（`startDate`〜`endDate`）、各テーマの指示文または質問文。日本語で150〜250文字程度（自由記述は200〜300文字程度）で簡潔に回答するよう指示する。

### 必要なセットアップ（開発者作業）

1. Google AI Studio（https://aistudio.google.com/）でGemini APIキーを取得し、Netlifyの環境変数`GEMINI_API_KEY`に設定する。
2. Firebaseコンソール → プロジェクト設定 → サービスアカウント → 「新しい秘密鍵の生成」でJSONを取得し、その内容（文字列化したJSON）をNetlifyの環境変数`FIREBASE_SERVICE_ACCOUNT`に設定する。
3. `netlify/functions/`ディレクトリに`package.json`を作成し`firebase-admin`を依存に追加する（実装タスクで対応）。
4. `netlify.toml`に`[functions]`セクションでディレクトリを指定する（実装タスクで対応）。

これらはコード側の実装が完了した後、デプロイ前にユーザー（開発者）自身が行う必要がある。

## エラー処理まとめ

- クライアント側fetch失敗・タイムアウト・Functionからの`error`レスポンス → toast表示、`aiLoading=false`
- Function側: Geminiからのレスポンスがテーマ提案モードで期待したJSON形式でない場合 → `{"error":"..."}`を返す
- Function側: Firebase IDトークン検証失敗 → `401`＋`{"error":"認証が必要です"}`
- Function側: `GEMINI_API_KEY`未設定など環境不備 → `500`＋`{"error":"..."}`

## スコープ外（将来検討）

- AI生成結果の再生成（同じテーマで再度生成し直すボタン）
- ユーザーごとの利用回数制限・レート制限
- AI生成メモの編集後の再生成連携
- 生成言語の切り替え（現状は日本語固定）

## 絵文字について

このプロジェクトの既存方針（タイムライン投稿機能等）を踏襲し、新規UI要素（AIモードトグル、ローディング表示等）に絵文字は使わず、SVGアイコン（`svgIcon()`/`ICONS`）を使用する。
