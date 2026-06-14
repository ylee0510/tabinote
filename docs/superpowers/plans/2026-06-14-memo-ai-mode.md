# メモタブ「AIモード」機能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** メモタブ（`renderNote`）に「AIモード」トグルとパネルを追加し、ログイン済みユーザーが「テーマ提案」または「自由記述（チャット風）」でAI（Gemini）に旅行先の情報を生成させ、見出し付きでメモに追加できるようにする。AI呼び出しは新規Netlify Function経由でGemini APIを呼び出し、Firebase IDトークンで認証する。

**Architecture:** `index.html`（バニラJS）に状態変数・テーマ定義・CSS・UI（AIモードトグル＋パネル）・クライアント側のAPI呼び出し関数を追加する。バックエンドは新規 `netlify/functions/ai-memo.js`（Node.js, Netlify Function）で、`firebase-admin`によるIDトークン検証後、Google Gemini REST APIを直接`fetch`で呼び出す。`netlify.toml`に`[functions]`設定を追加し、`netlify/functions/package.json`に`firebase-admin`を依存として追加する。

**Tech Stack:** Vanilla JS（ES5風、`Object.assign`/`.find`は既存コードでも使用済みのため利用可）、Firebase Firestore v8 compat、Firebase Auth（`user.getIdToken()`）、Netlify Functions（Node.js, `firebase-admin`、Gemini REST API）。

> **テストについて:** 本リポジトリにはテストランナー・package.jsonが無い（単一`index.html`）。フロントエンドの各タスクの「検証」はpreviewツール（`preview_start` / `preview_eval` / `preview_snapshot` / `preview_screenshot` / `preview_console_logs`）による手動フロー確認に置き換える。Netlify Function（Task 3）はpreview環境では実行できないため、`node --check`による構文確認のみ行う。実際の動作確認はNetlify環境変数設定後にユーザー自身が本番（gotavy.com）で行う（Task 4で案内する）。

参考: 設計仕様は `docs/superpowers/specs/2026-06-14-memo-ai-mode-design.md`（コミット済み）。

---

## File Structure

- **`index.html`**
  - 状態変数: `noteExtraBoxes`(596行付近)の並びに`showAiMode`/`aiThemes`/`aiQuestion`/`aiLoading`を追加。
  - アイコン: `ICONS`(1002〜1045行)に`sparkles`を追加。
  - テーマ定義: `function noteList(sel){`(1930行)の直前に`AI_THEME_DEFS`配列を追加。
  - CSS: `.note-readonly.note-block:last-child`(243行)の直後に`.note-ai-*`クラスを追加。
  - UI: `renderNote(sel)`(1941〜1974行)に AIモードトグル＋パネル表示を追加。
  - 新規関数: `renderAiPanel(sel)` / `callAiMemo(payload)` / `aiBasePayload()` / `generateAiThemes()` / `askAiQuestion()` を `renderNote` の直後に追加。
- **`netlify/functions/ai-memo.js`**（新規）: Netlify Function本体。
- **`netlify/functions/package.json`**（新規）: `firebase-admin`依存。
- **`netlify.toml`**（変更）: `[functions]`セクション追加。
- **`.gitignore`**（変更）: `netlify/functions/node_modules`を追加。

---

## Task 1: 状態変数・アイコン・テーマ定義・CSSの追加

このタスクでは見た目や挙動に影響する変更は行わない（土台の追加のみ）。

**Files:**
- Modify: `index.html`（596行付近 / 1002〜1045行 / 1930行付近 / 234〜243行）

- [ ] **Step 1: AIモード用の状態変数を追加**

596行目の直後に変数を追加する。

Before:
```javascript
var noteExtraBoxes=0; // メモタブ：保存済みメモに加えて表示する空の入力欄の数
```

After:
```javascript
var noteExtraBoxes=0; // メモタブ：保存済みメモに加えて表示する空の入力欄の数
var showAiMode=false; // メモタブAIモード：パネルの開閉
var aiThemes=[]; // メモタブAIモード：選択中のテーマキー配列
var aiQuestion=""; // メモタブAIモード：自由記述の入力値
var aiLoading=false; // メモタブAIモード：false=待機中／"themes"=テーマ提案生成中／"question"=自由記述回答生成中
```

- [ ] **Step 2: `ICONS`に`sparkles`を追加**

1044〜1045行目を変更する（`book`が`ICONS`オブジェクトの最後のエントリ）。

Before:
```javascript
  book:'<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>'
};
```

After:
```javascript
  book:'<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
  sparkles:'<path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275Z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/>'
};
```

- [ ] **Step 3: `AI_THEME_DEFS`配列を追加**

`function noteList(sel){`の直前に配列を追加する。

Before:
```javascript
function noteList(sel){
```

After:
```javascript
// メモタブ「AIモード」のテーマ定義（チップ表示・見出し・APIへの送信に使用）
var AI_THEME_DEFS=[
  {key:"history",label:"歴史"},
  {key:"language",label:"言語・あいさつ"},
  {key:"shops",label:"おすすめのお店・グルメ"},
  {key:"spots",label:"おすすめのスポット"},
  {key:"transport",label:"交通・移動"},
  {key:"safety",label:"治安・物価・注意事項"},
  {key:"food_culture",label:"食事・グルメ事情"},
  {key:"events",label:"イベント・祭り"}
];
function noteList(sel){
```

- [ ] **Step 4: AIモード用のCSSを追加**

243行目の直後にCSSを追加する。

Before:
```css
.note-readonly.note-block:last-child{border-bottom:none;margin-bottom:0;padding-bottom:0;}
```

After:
```css
.note-readonly.note-block:last-child{border-bottom:none;margin-bottom:0;padding-bottom:0;}
.note-ai-toggle{display:inline-flex;align-items:center;gap:6px;padding:7px 14px;background:var(--stamp);border:1.5px solid var(--border);border-radius:16px;font-size:13px;font-weight:700;color:var(--accent);cursor:pointer;font-family:inherit;margin-bottom:12px;}
.note-ai-toggle.on{background:var(--accent);border-color:var(--accent);color:#fff;}
.note-ai-panel{background:var(--stamp);border:1.5px solid var(--border);border-radius:12px;padding:14px;margin-bottom:14px;}
.note-ai-section-label{font-size:12px;font-weight:700;color:var(--muted);margin-bottom:8px;}
.note-ai-chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px;}
.note-ai-chip{background:var(--paper);border:1.5px solid var(--border);border-radius:16px;padding:5px 12px;font-size:12px;font-weight:600;color:var(--muted);cursor:pointer;font-family:inherit;}
.note-ai-chip.on{background:#dbeafe;border-color:#1d4ed8;color:#1d4ed8;}
.note-ai-ask{display:flex;gap:8px;margin-top:12px;}
.note-ai-ask .finp{flex:1;}
```

- [ ] **Step 5: 構文確認（preview）**

Run: `preview_start`（既存サーバが動いていれば`preview_eval: window.location.reload()`）。
その後`preview_console_logs`（level "error"）を確認。
Expected: 新規の構文エラー・参照エラーが出ないこと。この時点ではUIへの参照がまだ無いため、見た目の変化は無い。

- [ ] **Step 6: コミット**

```bash
git add index.html
git commit -m "feat: メモタブAIモード用の状態変数・アイコン・テーマ定義・CSSを追加"
```

---

## Task 2: メモタブにAIモードのトグル・パネルUIとAI呼び出し処理を追加

**Files:**
- Modify: `index.html`（`renderNote`関数 1941〜1974行付近、およびその直後）

- [ ] **Step 1: `renderNote`にAIモードトグルとパネル表示を追加**

`.note-hint`を追加している行の直後（`var boxCount=...`の手前）に追加する。

Before:
```javascript
function renderNote(sel){
  var d=ce("div","content");
  var notes=noteList(sel);
  if(isViewOnly){
    var shown=notes.filter(function(n){return (n||"").trim()!=="";});
    if(shown.length===0){var ro=ce("div","note-readonly");ap(ro,tx("（メモはありません）"));ap(d,ro);return d;}
    shown.forEach(function(n){var ro=ce("div","note-readonly note-block");ap(ro,tx(n));ap(d,ro);});
    return d;
  }
  ap(d,ap(ce("div","note-hint"),tx("旅する国や街の歴史・言葉や気に入ったお店、気づいたことなど、自由に書き残せるノートです。タイムラインにも公開できます。")));
  var boxCount=Math.max(1,notes.length+noteExtraBoxes);
```

After:
```javascript
function renderNote(sel){
  var d=ce("div","content");
  var notes=noteList(sel);
  if(isViewOnly){
    var shown=notes.filter(function(n){return (n||"").trim()!=="";});
    if(shown.length===0){var ro=ce("div","note-readonly");ap(ro,tx("（メモはありません）"));ap(d,ro);return d;}
    shown.forEach(function(n){var ro=ce("div","note-readonly note-block");ap(ro,tx(n));ap(d,ro);});
    return d;
  }
  ap(d,ap(ce("div","note-hint"),tx("旅する国や街の歴史・言葉や気に入ったお店、気づいたことなど、自由に書き残せるノートです。タイムラインにも公開できます。")));
  if(!isGuest&&user){
    var aiBtn=ce("button","note-ai-toggle"+(showAiMode?" on":""),{type:"button",onclick:function(){showAiMode=!showAiMode;render();}});
    ap(aiBtn,svgIcon("sparkles","currentColor",15),tx("AIモード"));
    ap(d,aiBtn);
    if(showAiMode)ap(d,renderAiPanel(sel));
  }
  var boxCount=Math.max(1,notes.length+noteExtraBoxes);
```

- [ ] **Step 2: `renderAiPanel`とAI呼び出し関数を追加**

`renderNote`の直後（`function mkCurSelect(current, onchange){`の手前）に追加する。

Before:
```javascript
  ap(d,ap(ce("button","note-add-btn",{onclick:function(){noteExtraBoxes++;render();}}),tx("＋ 追加")));
  return d;
}
function mkCurSelect(current, onchange){
```

After:
```javascript
  ap(d,ap(ce("button","note-add-btn",{onclick:function(){noteExtraBoxes++;render();}}),tx("＋ 追加")));
  return d;
}
function renderAiPanel(sel){
  var panel=ce("div","note-ai-panel");
  ap(panel,ap(ce("div","note-ai-section-label"),tx("テーマを選んでAIに提案してもらう")));
  var chips=ce("div","note-ai-chips");
  AI_THEME_DEFS.forEach(function(t){
    var on=aiThemes.indexOf(t.key)>=0;
    var chip=ce("button","note-ai-chip"+(on?" on":""),{type:"button",onclick:function(){
      var i=aiThemes.indexOf(t.key);
      if(i>=0)aiThemes.splice(i,1);else aiThemes.push(t.key);
      render();
    }});
    ap(chip,tx(t.label));
    ap(chips,chip);
  });
  ap(panel,chips);
  var genBtn=ce("button","btn-ok",{type:"button",style:{width:"100%",border:"none"},onclick:function(){generateAiThemes();}});
  genBtn.disabled=!!aiLoading||aiThemes.length===0;
  ap(genBtn,tx(aiLoading==="themes"?"生成中...":"AIで提案"));
  ap(panel,genBtn);
  ap(panel,ap(ce("div","note-ai-section-label",{style:{marginTop:"14px"}}),tx("AIに質問する")));
  var askRow=ce("div","note-ai-ask");
  var input=ce("input","finp",{type:"text",maxlength:"200",placeholder:"例: 子連れでも楽しめるスポットは？"});
  input.value=aiQuestion;
  input.disabled=!!aiLoading;
  var askBtn=ce("button","btn-ok",{type:"button",style:{flex:"0 0 auto",border:"none"},onclick:function(){askAiQuestion();}});
  askBtn.disabled=!!aiLoading||!aiQuestion.trim();
  input.oninput=function(){aiQuestion=input.value;askBtn.disabled=!!aiLoading||!aiQuestion.trim();};
  ap(askBtn,tx(aiLoading==="question"?"生成中...":"聞く"));
  ap(askRow,input,askBtn);
  ap(panel,askRow);
  return panel;
}
async function callAiMemo(payload){
  var token=await user.getIdToken();
  var res=await fetch("/.netlify/functions/ai-memo",{
    method:"POST",
    headers:{"Content-Type":"application/json","Authorization":"Bearer "+token},
    body:JSON.stringify(payload)
  });
  var data;
  try{data=await res.json();}catch(e){data={};}
  if(!res.ok||data.error)throw new Error(data.error||"AI生成に失敗しました");
  return data;
}
function aiBasePayload(){
  var sel=getSel()||{};
  return {destination:sel.destination||"",regions:sel.regions||[],type:sel.type||"overseas",startDate:sel.startDate||"",endDate:sel.endDate||""};
}
async function generateAiThemes(){
  if(aiLoading||aiThemes.length===0)return;
  aiLoading="themes";render();
  try{
    var payload=Object.assign(aiBasePayload(),{mode:"themes",themes:aiThemes.slice()});
    var data=await callAiMemo(payload);
    var sel=getSel();
    if(sel){
      var notes=noteList(sel).slice();
      (data.results||[]).forEach(function(r){
        var def=AI_THEME_DEFS.find(function(t){return t.key===r.theme;});
        var label=def?def.label:r.theme;
        notes.push("【"+label+"】(AI生成)\n"+r.text);
      });
      noteExtraBoxes=0;
      aiThemes=[];
      await upd({note:notes});
    }
  }catch(e){
    console.error(e);
    toast("AI生成に失敗しました。しばらくしてから再度お試しください。");
  }finally{
    aiLoading=false;render();
  }
}
async function askAiQuestion(){
  var q=aiQuestion.trim();
  if(aiLoading||!q)return;
  aiLoading="question";render();
  try{
    var payload=Object.assign(aiBasePayload(),{mode:"question",question:q});
    var data=await callAiMemo(payload);
    var sel=getSel();
    if(sel){
      var notes=noteList(sel).slice();
      notes.push("【AIへの質問: "+q+"】(AI生成)\n"+(data.answer||""));
      noteExtraBoxes=0;
      aiQuestion="";
      await upd({note:notes});
    }
  }catch(e){
    console.error(e);
    toast("AI生成に失敗しました。しばらくしてから再度お試しください。");
  }finally{
    aiLoading=false;render();
  }
}
function mkCurSelect(current, onchange){
```

- [ ] **Step 3: 動作確認（preview）**

Run: `preview_eval: window.location.reload()`

1. ログイン済みユーザーで旅行詳細を開き「メモ」タブを表示 → `.note-hint`の下に`sparkles`アイコン＋「AIモード」トグルが表示される。
2. トグルをクリック → AIパネルが開く（8個のテーマチップ「歴史」「言語・あいさつ」「おすすめのお店・グルメ」「おすすめのスポット」「交通・移動」「治安・物価・注意事項」「食事・グルメ事情」「イベント・祭り」＋「AIで提案」ボタン＋「AIに質問する」見出し＋自由記述欄＋「聞く」ボタン）。再クリックで閉じる。
3. テーマ未選択時は「AIで提案」が無効化されている。チップをクリックすると選択状態（背景が青系`#dbeafe`に変化）になり「AIで提案」が有効化される。再クリックで選択解除すると再び無効化される。
4. 自由記述欄が空の時は「聞く」が無効化されている。テキストを入力すると有効化される。
5. テーマを1つ選択して「AIで提案」をクリック → ボタンラベルが「生成中...」に変わり、「AIで提案」「聞く」両ボタンが無効化される。バックエンド未実装（Task 3で実装）のためリクエストは失敗し、最終的にトースト「AI生成に失敗しました。しばらくしてから再度お試しください。」が表示され、ボタンが元の状態（ラベル「AIで提案」、選択中テーマが残っていれば有効）に戻る。`console.error`によるエラーログがこの時点で1件出るのは想定どおり（キャッチ済みのエラー）。
6. ゲストモードでは「メモ」タブに「AIモード」トグルが表示されない。
7. `preview_screenshot`でAIモードパネルを撮影（テーマ選択済み状態）。
8. `preview_console_logs`（level "error"）を確認し、Step 5の想定済みエラー以外の新規エラーが無いことを確認。

- [ ] **Step 4: コミット**

```bash
git add index.html
git commit -m "feat: メモタブにAIモード（テーマ提案・自由記述）のUIを追加"
```

---

## Task 3: Netlify Function バックエンド（`ai-memo.js`）の実装

**Files:**
- Create: `netlify/functions/ai-memo.js`
- Create: `netlify/functions/package.json`
- Modify: `netlify.toml`
- Modify: `.gitignore`

- [ ] **Step 1: `netlify/functions/ai-memo.js`を作成**

```javascript
const admin = require("firebase-admin");

let firebaseApp;
function getFirebaseApp() {
  if (!firebaseApp) {
    const serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
    firebaseApp = admin.initializeApp({
      credential: admin.credential.cert(serviceAccount)
    });
  }
  return firebaseApp;
}

// テーマキー -> AIへの指示内容（プロンプトに使用）
const THEME_PROMPTS = {
  history: "その土地の歴史的背景・史跡",
  language: "現地で使われている言語、簡単なあいさつ・言い回し",
  shops: "具体的な店名を含むおすすめのレストラン・ショップ",
  spots: "定番から少し外れた訪れる価値のある場所",
  transport: "電車・バス・タクシー事情、ICカードなど",
  safety: "治安状況、物価感（食事・交通などの目安）、旅行者が気をつけるべき点",
  food_culture: "食文化、チップ習慣、食事マナーなど（おすすめのお店とは別観点）",
  events: "旅行期間に合った現地のイベント・祭り"
};

function tripContextText(body) {
  const lines = [];
  if (body.destination) lines.push("旅行先: " + body.destination);
  if (Array.isArray(body.regions) && body.regions.length) lines.push("地域: " + body.regions.join("、"));
  lines.push("旅行種別: " + (body.type === "domestic" ? "国内旅行" : "海外旅行"));
  if (body.startDate) lines.push("旅行期間: " + body.startDate + (body.endDate ? " 〜 " + body.endDate : ""));
  return lines.join("\n");
}

function resp(statusCode, bodyObj) {
  return {
    statusCode: statusCode,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(bodyObj)
  };
}

async function callGemini(prompt, opts) {
  const model = process.env.GEMINI_MODEL || "gemini-2.5-flash";
  const url = "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent?key=" + process.env.GEMINI_API_KEY;

  const generationConfig = { maxOutputTokens: opts.maxOutputTokens || 500 };
  if (opts.responseMimeType) generationConfig.responseMimeType = opts.responseMimeType;

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      contents: [{ parts: [{ text: prompt }] }],
      generationConfig: generationConfig
    })
  });

  if (!res.ok) {
    const errBody = await res.text();
    throw new Error("Gemini API error: " + res.status + " " + errBody);
  }

  const data = await res.json();
  const text = data && data.candidates && data.candidates[0] && data.candidates[0].content &&
    data.candidates[0].content.parts && data.candidates[0].content.parts[0] &&
    data.candidates[0].content.parts[0].text;
  if (!text) throw new Error("Gemini API returned no text");
  return text;
}

async function handleThemes(body) {
  const themes = Array.isArray(body.themes) ? body.themes.filter(function (t) { return THEME_PROMPTS[t]; }) : [];
  if (themes.length === 0) return resp(400, { error: "themesが不正です" });

  const context = tripContextText(body);
  const instructions = themes.map(function (key) {
    return "- " + key + ": " + THEME_PROMPTS[key];
  }).join("\n");

  const prompt = context + "\n\n" +
    "上記の旅行に関する情報をもとに、以下の各テーマについて日本語で150〜250文字程度で説明してください。\n" +
    instructions + "\n\n" +
    "出力は必ず次のJSON形式のみで返してください（説明文や前置き、コードブロック記号は不要）:\n" +
    '{"results":[{"theme":"テーマキー","text":"本文"}]}';

  const maxTokens = themes.length * 300;
  const raw = await callGemini(prompt, { responseMimeType: "application/json", maxOutputTokens: maxTokens });

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (e) {
    return resp(500, { error: "AIの応答を解析できませんでした" });
  }
  if (!parsed || !Array.isArray(parsed.results)) {
    return resp(500, { error: "AIの応答を解析できませんでした" });
  }
  return resp(200, { results: parsed.results });
}

async function handleQuestion(body) {
  const question = (body.question || "").trim();
  if (!question) return resp(400, { error: "questionが不正です" });

  const context = tripContextText(body);
  const prompt = context + "\n\n" +
    "上記の旅行に関する次の質問に、日本語で200〜300文字程度で回答してください。\n" +
    "質問: " + question;

  const text = await callGemini(prompt, { maxOutputTokens: 500 });
  return resp(200, { answer: text.trim() });
}

exports.handler = async function (event) {
  if (event.httpMethod !== "POST") {
    return resp(405, { error: "Method Not Allowed" });
  }

  if (!process.env.FIREBASE_SERVICE_ACCOUNT || !process.env.GEMINI_API_KEY) {
    return resp(500, { error: "サーバー設定が不完全です" });
  }

  const authHeader = event.headers.authorization || event.headers.Authorization || "";
  const token = authHeader.replace(/^Bearer\s+/i, "");
  if (!token) return resp(401, { error: "認証が必要です" });

  try {
    await getFirebaseApp().auth().verifyIdToken(token);
  } catch (e) {
    return resp(401, { error: "認証が必要です" });
  }

  let body;
  try {
    body = JSON.parse(event.body || "{}");
  } catch (e) {
    return resp(400, { error: "リクエストの形式が正しくありません" });
  }

  try {
    if (body.mode === "themes") return await handleThemes(body);
    if (body.mode === "question") return await handleQuestion(body);
    return resp(400, { error: "modeが不正です" });
  } catch (e) {
    console.error(e);
    return resp(500, { error: "AI生成に失敗しました" });
  }
};
```

- [ ] **Step 2: `netlify/functions/package.json`を作成**

```json
{
  "name": "tavy-ai-memo-function",
  "private": true,
  "dependencies": {
    "firebase-admin": "^12.0.0"
  }
}
```

- [ ] **Step 3: `netlify.toml`に`[functions]`設定を追加**

Before:
```toml
[[headers]]
  for = "/*"
  [headers.values]
    Content-Security-Policy = "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:;"
    X-Frame-Options = "SAMEORIGIN"
```

After:
```toml
[functions]
  directory = "netlify/functions"
  node_bundler = "esbuild"

[[headers]]
  for = "/*"
  [headers.values]
    Content-Security-Policy = "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:;"
    X-Frame-Options = "SAMEORIGIN"
```

- [ ] **Step 4: `.gitignore`に`netlify/functions/node_modules`を追加**

Before:
```
.DS_Store
.superpowers/
.claude/
```

After:
```
.DS_Store
.superpowers/
.claude/
netlify/functions/node_modules/
```

- [ ] **Step 5: 構文確認**

Run: `node --check netlify/functions/ai-memo.js`
Expected: 何も出力されず終了コード0（構文エラーが無い）。

Run: `node -e "JSON.parse(require('fs').readFileSync('netlify/functions/package.json','utf8'));console.log('ok')"`
Expected: `ok`が出力される（JSONとして正しい）。

- [ ] **Step 6: コミット**

```bash
git add netlify/functions/ai-memo.js netlify/functions/package.json netlify.toml .gitignore
git commit -m "feat: メモタブAIモード用のNetlify Function（Gemini連携）を追加"
```

---

## Task 4: 全体動作確認・セットアップ案内・デプロイ

- [ ] **Step 1: エンドツーエンド確認（preview）**

Run: `preview_eval: window.location.reload()`。設計仕様（`docs/superpowers/specs/2026-06-14-memo-ai-mode-design.md`）の検証項目を順に確認し、`preview_console_logs`（level "error"）でTask 2 Step 3で確認済みのエラー以外の新規エラーが無いこと:

1. ログイン済みユーザーでメモタブを開く → 「AIモード」トグルが表示され、開閉できる。
2. 複数テーマ（例: 「歴史」「おすすめのスポット」）を選択して「AIで提案」→ ローディング状態（両ボタン無効化・「生成中...」表示）→ バックエンドの環境変数未設定のため失敗 → エラートースト表示 → ボタンが元の状態に戻る（選択中テーマは保持されたまま）。
3. 自由記述欄に質問を入力して「聞く」→ 同様にローディング→エラートースト→元の状態に戻る（入力内容は保持されたまま）。
4. ゲストモード・閲覧専用リンクでは「AIモード」トグルが表示されない。
5. 画面に絵文字が使われていないこと（「AIモード」トグルは`sparkles`アイコンのみ）。

- [ ] **Step 2: 最終スクリーンショット**

Run: `preview_screenshot`（メモタブ通常表示・AIモードパネル展開・テーマ選択状態 各1枚）。ユーザーへ提示。

- [ ] **Step 3: セットアップ案内とpush**

このステップはサブエージェントではなくコントローラー（メインセッション）が実施する。ユーザーに以下を提示する:

1. 今回のコード変更内容のサマリー。
2. 本番で動作させるために**ユーザー自身がNetlifyの管理画面で行う必要がある作業**（設計仕様の「必要なセットアップ」に対応）:
   - Google AI Studio（https://aistudio.google.com/）でGemini APIキーを取得し、Netlifyの環境変数`GEMINI_API_KEY`に設定する。
   - Firebaseコンソール → プロジェクト設定 → サービスアカウント →「新しい秘密鍵の生成」でJSONを取得し、その内容（JSON文字列そのもの）をNetlifyの環境変数`FIREBASE_SERVICE_ACCOUNT`に設定する。
   - （任意）`GEMINI_MODEL`環境変数でモデル名を上書きできる（未設定時は`gemini-2.5-flash`）。
3. 上記環境変数が未設定の間は、AIモードの「AIで提案」「聞く」はエラートーストになる（フォールバックは正常動作・既存のメモ機能には影響なし）ことを説明する。
4. pushの許可を得てから`git push origin main`を実行し、Netlifyへのデプロイをトリガーする。
5. 環境変数設定後、ユーザー自身が本番（gotavy.com）でログインしAIモードを試すよう案内する。

---

## Self-Review チェック結果

- **設計仕様カバレッジ**: UI配置・トグル（Task 2 Step1）、テーマチップ・提案ボタン・自由記述・ローディング（Task 2 Step2）、生成結果の挿入形式とリセット（Task 2 Step2の`generateAiThemes`/`askAiQuestion`）、`AI_THEME_DEFS`8テーマ（Task 1 Step3）、新規状態変数（Task 1 Step1）、`sparkles`アイコン（Task 1 Step2）、Netlify Function本体・認証・リクエスト/レスポンス契約・Gemini呼び出し（Task 3）、必要なセットアップ案内（Task 4 Step3）、エラー処理（Task 2 Step2のtry/catch/finally、Task 3のFunction側エラー分岐）を全てカバー。スコープ外項目（再生成・レート制限・編集後再生成・言語切替）は実装対象外のまま。
- **プレースホルダー確認**: TBD/TODO等は無し。各コードブロックは完全な実装。
- **型・命名の一貫性**: `aiLoading`は`false|"themes"|"question"`（design docの「ローディング中はAIで提案・聞くボタンを無効化し、押されたボタンのラベルを生成中...にする」要件を満たすための具体化。設計仕様の「boolean」という記述より一段詳細だが、`if(aiLoading)`は真偽値として機能するため矛盾しない）。`AI_THEME_DEFS`のキー（`history`/`language`/`shops`/`spots`/`transport`/`safety`/`food_culture`/`events`）はTask1（クライアント）とTask3（`THEME_PROMPTS`、サーバー側）で一致。`noteList`/`upd`/`getSel`/`toast`/`svgIcon`/`ICONS`は既存関数をそのまま使用。
