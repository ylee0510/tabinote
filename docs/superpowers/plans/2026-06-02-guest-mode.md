# Guest Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 未ログインユーザーがワールドカップ2026のデモデータでアプリをお試しできるゲストモードを追加する。

**Architecture:** `index.html` 単一ファイルに `isGuest` フラグと `DEMO_TRIPS` 定数を追加する。ログイン画面に「ログインせずに試す」ボタンを追加し、クリックで `isGuest=true` + デモデータセット + `render()`。書き込み関数は先頭で `isGuest` チェックしてトーストを出して早期 return。`auth.onAuthStateChanged` でログイン時にゲスト状態をクリアして通常フローへ移行。

**Tech Stack:** Vanilla HTML/CSS/JS、Firebase Auth/Firestore（変更なし）

---

### Task 1: DEMO_TRIPS 定数と isGuest 変数を追加

**Files:**
- Modify: `index.html` — グローバル変数宣言部（line 268付近）とその直前

- [ ] **Step 1: `DEMO_TRIPS` 定数を DEFAULT_TEMPLATES の直後（line 267付近）に追加する**

line 267（`};` — DEFAULT_TEMPLATES の閉じ括弧）の直後に以下を挿入する:

```js
var DEMO_TRIPS=[{
  id:"demo-wc2026",
  name:"World Cup 2026 🏆",
  destination:"ダラス / モンテレイ / ラスベガス",
  startDate:"2026-06-12",
  endDate:"2026-06-27",
  type:"overseas",
  currency:"USD",
  ownerId:"guest",
  ownerName:"ゲスト",
  memberIds:["guest"],
  members:[{uid:"guest",name:"ゲスト",email:""}],
  itinerary:[
    {id:"di1",date:"2026-06-12",time:"10:00",type:"出発",text:"成田空港発 → ダラス着（NH108便）"},
    {id:"di2",date:"2026-06-12",time:"20:00",type:"チェックイン",text:"ホテルチェックイン（Dallas Marriott）"},
    {id:"di3",date:"2026-06-13",time:"10:00",type:"観光",text:"ダラス市内観光・AT&Tスタジアム下見"},
    {id:"di4",date:"2026-06-14",time:"15:00",type:"観光",text:"🇯🇵 vs 🇳🇱（AT&T Stadium, Dallas）"},
    {id:"di5",date:"2026-06-15",time:"09:00",type:"移動",text:"ダラス → ラスベガス（国内線）"},
    {id:"di6",date:"2026-06-15",time:"14:00",type:"チェックイン",text:"ホテルチェックイン（Las Vegas）"},
    {id:"di7",date:"2026-06-16",time:"10:00",type:"観光",text:"ラスベガス観光"},
    {id:"di8",date:"2026-06-17",time:"07:00",type:"移動",text:"ラスベガス → グランドキャニオン（レンタカー）"},
    {id:"di9",date:"2026-06-17",time:"11:00",type:"観光",text:"グランドキャニオン展望台観光"},
    {id:"di10",date:"2026-06-18",time:"09:00",type:"観光",text:"グランドキャニオン観光"},
    {id:"di11",date:"2026-06-18",time:"17:00",type:"移動",text:"グランドキャニオン → ラスベガス"},
    {id:"di12",date:"2026-06-19",time:"10:00",type:"移動",text:"ラスベガス → モンテレイ（国際線）"},
    {id:"di13",date:"2026-06-19",time:"18:00",type:"チェックイン",text:"ホテルチェックイン（Monterrey）"},
    {id:"di14",date:"2026-06-20",time:"22:00",type:"観光",text:"🇯🇵 vs 🇹🇳（Estadio BBVA, Monterrey）"},
    {id:"di15",date:"2026-06-21",time:"10:00",type:"移動",text:"モンテレイ → ダラス（国内線）"},
    {id:"di16",date:"2026-06-21",time:"16:00",type:"チェックイン",text:"ホテルチェックイン（Dallas）"},
    {id:"di17",date:"2026-06-22",time:"10:00",type:"観光",text:"ダラス観光"},
    {id:"di18",date:"2026-06-25",time:"18:00",type:"観光",text:"🇯🇵 vs 🇸🇪（AT&T Stadium, Dallas）"},
    {id:"di19",date:"2026-06-26",time:"11:00",type:"出発",text:"ダラス発 → 帰国便（NH109便）"},
    {id:"di20",date:"2026-06-27",time:"16:00",type:"到着",text:"成田着"}
  ],
  packing:[
    {id:"dp1",text:"パスポート",checked:false,memo:""},
    {id:"dp2",text:"航空券（eチケット）",checked:false,memo:""},
    {id:"dp3",text:"海外保険証",checked:false,memo:""},
    {id:"dp4",text:"外貨・クレジットカード",checked:false,memo:""},
    {id:"dp5",text:"充電器（変換プラグ）",checked:false,memo:""},
    {id:"dp6",text:"常備薬",checked:false,memo:""},
    {id:"dp7",text:"着替え",checked:false,memo:""},
    {id:"dp8",text:"日本代表ユニフォーム",checked:false,memo:""},
    {id:"dp9",text:"観戦チケット（3試合分）",checked:false,memo:""},
    {id:"dp10",text:"双眼鏡",checked:false,memo:""},
    {id:"dp11",text:"日焼け止め",checked:false,memo:""}
  ],
  todo:[],
  places:[],
  budget:[
    {id:"db1",icon:"✈️",name:"航空券",budget_A:400000,actual_A:0,budget_B:0,actual_B:0},
    {id:"db2",icon:"🏨",name:"宿泊費",budget_A:200000,actual_A:0,budget_B:0,actual_B:0},
    {id:"db3",icon:"🚇",name:"現地交通費",budget_A:50000,actual_A:0,budget_B:0,actual_B:0},
    {id:"db4",icon:"🍜",name:"食費",budget_A:80000,actual_A:0,budget_B:0,actual_B:0},
    {id:"db5",icon:"🎡",name:"観光・体験",budget_A:50000,actual_A:0,budget_B:0,actual_B:0},
    {id:"db6",icon:"🎟",name:"観戦チケット",budget_A:150000,actual_A:0,budget_B:0,actual_B:0},
    {id:"db7",icon:"🛍",name:"お土産",budget_A:30000,actual_A:0,budget_B:0,actual_B:0},
    {id:"db8",icon:"💊",name:"保険・その他",budget_A:40000,actual_A:0,budget_B:0,actual_B:0}
  ],
  currencies:{A:"JPY",B:"USD"}
}];
```

- [ ] **Step 2: `isGuest` 変数を既存のグローバル変数宣言行（line 277付近）に追加する**

**変更前:**
```js
var isViewOnly=false,viewOnlyTrip=null;
```

**変更後:**
```js
var isViewOnly=false,viewOnlyTrip=null;
var isGuest=false;
```

- [ ] **Step 3: 構文エラーがないことを確認する**

ブラウザで開き、コンソールにJS構文エラーが出ないことを確認する。

- [ ] **Step 4: コミットする**

```bash
git add index.html
git commit -m "feat: add DEMO_TRIPS constant and isGuest flag"
```

---

### Task 2: CSS — ゲストバナースタイルを追加

**Files:**
- Modify: `index.html` — `<style>` ブロック末尾（`</style>` の直前）

- [ ] **Step 1: ゲストバナー用CSSを追加する**

`</style>` の直前（現在 line 154付近の `.hero{...}` の後）に以下を追加する:

```css
.guest-banner{background:#f4f4f5;border-bottom:1px solid var(--border);padding:7px 16px;display:flex;align-items:center;justify-content:space-between;font-size:11px;color:var(--muted);}
.guest-banner-btn{background:var(--accent);color:#fff;border:none;border-radius:8px;padding:4px 10px;font-size:11px;font-weight:700;cursor:pointer;font-family:inherit;}
.guest-try-btn{background:none;border:none;color:var(--accent);font-size:13px;font-weight:700;cursor:pointer;font-family:inherit;margin-top:16px;padding:8px 0;text-decoration:underline;}
```

- [ ] **Step 2: コミットする**

```bash
git add index.html
git commit -m "feat: add guest banner CSS styles"
```

---

### Task 3: ログイン画面に「ログインせずに試す」ボタン追加

**Files:**
- Modify: `index.html` — `renderLogin()` 関数（line 439〜449）

- [ ] **Step 1: `renderLogin()` を変更して「ログインせずに試す」ボタンを追加する**

**変更前（line 448）:**
```js
  ap(gb,svg,tx("Googleでログイン"));ap(d,gb);return d;
```

**変更後:**
```js
  ap(gb,svg,tx("Googleでログイン"));ap(d,gb);
  var tryBtn=ce("button","guest-try-btn",{onclick:function(){isGuest=true;trips=DEMO_TRIPS.slice();selId="demo-wc2026";view="detail";activeTab="itinerary";render();}});
  ap(tryBtn,tx("ログインせずに試す →"));
  ap(d,tryBtn);
  return d;
```

- [ ] **Step 2: ブラウザで動作確認する**

1. ページを開きログイン画面を表示する
2. 「ログインせずに試す →」ボタンが表示されることを確認
3. クリックするとデモ旅行（World Cup 2026 🏆）が表示されることを確認
4. 行程タブにデモデータが表示されることを確認

- [ ] **Step 3: コミットする**

```bash
git add index.html
git commit -m "feat: add 'try without login' button to login screen"
```

---

### Task 4: render() にゲスト対応とゲストバナーを追加

**Files:**
- Modify: `index.html` — `render()` 関数（line 391〜440付近）

- [ ] **Step 1: `render()` の `!user` チェックを `isGuest` 対応に変更する**

**変更前（line 402付近）:**
```js
  if(!user){ap(app,renderLogin());return;}
```

**変更後:**
```js
  if(!user&&!isGuest){ap(app,renderLogin());return;}
```

- [ ] **Step 2: `render()` 内でゲストバナーを表示する**

`renderHeader()` を呼ぶ直後にゲストバナーを追加する。

**変更前（line 403〜407付近）:**
```js
  var isWide=window.innerWidth>=768;
  var wrap=ce("div","");
  var hdr=renderHeader();
  if(isWide&&view==="detail")hdr.classList.add("pc-hide-back");
  ap(wrap,hdr);
```

**変更後:**
```js
  var isWide=window.innerWidth>=768;
  var wrap=ce("div","");
  var hdr=renderHeader();
  if(isWide&&view==="detail")hdr.classList.add("pc-hide-back");
  ap(wrap,hdr);
  if(isGuest){
    var banner=ce("div","guest-banner");
    ap(banner,tx("👤 ゲストモード｜ログインすると旅行を保存できます"));
    var loginBtn=ce("button","guest-banner-btn",{onclick:function(){isGuest=false;trips=[];selId=null;view="list";render();}});
    ap(loginBtn,tx("ログイン"));
    ap(banner,loginBtn);
    ap(wrap,banner);
  }
```

- [ ] **Step 3: `renderHeader()` の `user.uid` 参照を null ガードする（line 465付近）**

ゲストモードでは `user` が `null` のため、シェアボタン表示条件でエラーになる。

**変更前:**
```js
if(sel&&sel.ownerId===user.uid)ap(r,ap(ce("button","icon-btn2",{onclick:function(){showShare=true;render();}}),tx("🔗")));
```

**変更後:**
```js
if(sel&&user&&sel.ownerId===user.uid)ap(r,ap(ce("button","icon-btn2",{onclick:function(){showShare=true;render();}}),tx("🔗")));
```

- [ ] **Step 4: ブラウザで確認する**

1. 「ログインせずに試す」でゲストモードに入り、ヘッダー下にバナーが表示されることを確認
2. バナーの「ログイン」ボタンでログイン画面に戻ることを確認
3. コンソールに TypeError が出ないことを確認

- [ ] **Step 4: コミットする**

```bash
git add index.html
git commit -m "feat: guest mode gate in render() and guest banner"
```

---

### Task 5: 書き込み関数にゲストガードを追加

**Files:**
- Modify: `index.html` — `upd()`, `createTrip()`, `deleteTrip()`, `addCheck()`, `addPlace()`, `confirmPin()`, `saveTpl()`, `addBudgetItem()` 各関数

- [ ] **Step 1: `upd()` にゲストガードを追加する（line 309付近）**

**変更前:**
```js
async function upd(patch){var sel=getSel();if(!sel)return;await db.collection("trips").doc(sel.id).update(patch);}
```

**変更後:**
```js
async function upd(patch){if(isGuest){toast("💡 保存するにはログインが必要です");return;}var sel=getSel();if(!sel)return;await db.collection("trips").doc(sel.id).update(patch);}
```

- [ ] **Step 2: `createTrip()` にゲストガードを追加する（line 310付近）**

**変更前:**
```js
async function createTrip(){if(!tripForm.name.trim()||saving||!user)return;
```

**変更後:**
```js
async function createTrip(){if(isGuest){toast("💡 保存するにはログインが必要です");return;}if(!tripForm.name.trim()||saving||!user)return;
```

- [ ] **Step 3: `deleteTrip()` にゲストガードを追加する（line 311付近）**

**変更前:**
```js
async function deleteTrip(id){if(!confirm("この旅行を削除しますか？"))return;
```

**変更後:**
```js
async function deleteTrip(id){if(isGuest){toast("💡 保存するにはログインが必要です");return;}if(!confirm("この旅行を削除しますか？"))return;
```

- [ ] **Step 4: `addCheck()` にゲストガードを追加する**

`addCheck` 関数を検索（`function addCheck`）し、先頭に追加する。

**変更前:**
```js
async function addCheck(tab){if(!checkInput.trim())return;
```

**変更後:**
```js
async function addCheck(tab){if(isGuest){toast("💡 保存するにはログインが必要です");return;}if(!checkInput.trim())return;
```

- [ ] **Step 5: `addPlace()` にゲストガードを追加する**

**変更前:**
```js
async function addPlace(){var name=placeInput.trim();if(!name)return;
```

**変更後:**
```js
async function addPlace(){if(isGuest){toast("💡 保存するにはログインが必要です");return;}var name=placeInput.trim();if(!name)return;
```

- [ ] **Step 6: `confirmPin()` にゲストガードを追加する**

**変更前:**
```js
async function confirmPin(){if(!pinName.trim()||!pendingPin)return;
```

**変更後:**
```js
async function confirmPin(){if(isGuest){toast("💡 保存するにはログインが必要です");return;}if(!pinName.trim()||!pendingPin)return;
```

- [ ] **Step 7: `saveTpl()` にゲストガードを追加する**

**変更前:**
```js
async function saveTpl(next){templates=next;try{await db.collection("users")
```

**変更後:**
```js
async function saveTpl(next){if(isGuest){toast("💡 保存するにはログインが必要です");return;}templates=next;try{await db.collection("users")
```

- [ ] **Step 8: `addBudgetItem()` にゲストガードを追加する**

**変更前:**
```js
async function addBudgetItem(){
  if(!newBudget.name.trim())return;
```

**変更後:**
```js
async function addBudgetItem(){
  if(isGuest){toast("💡 保存するにはログインが必要です");return;}
  if(!newBudget.name.trim())return;
```

- [ ] **Step 9: ゲストモードで各操作のトーストを確認する**

ゲストモードで以下を試し、すべて「💡 保存するにはログインが必要です」トーストが出ることを確認:
- 行程に項目を追加しようとする
- 荷物をチェックしようとする
- 予算項目を編集しようとする

- [ ] **Step 10: コミットする**

```bash
git add index.html
git commit -m "feat: guard all write functions for guest mode"
```

---

### Task 6: auth.onAuthStateChanged でゲスト状態をクリアし、デプロイ

**Files:**
- Modify: `index.html` — `auth.onAuthStateChanged` コールバック（line 1004〜1011）

- [ ] **Step 1: ログイン時にゲスト状態をクリアする**

**変更前（line 1004〜1011）:**
```js
auth.onAuthStateChanged(function(u){
  user=u;
  var sharedId=getSharedId();
  if(sharedId&&!isViewOnly){loadSharedTrip(sharedId);return;}
  if(u){subscribeTrips();subscribeTemplates();loadProfile();}
  else{if(tripsUnsub){tripsUnsub();tripsUnsub=null;}if(tplUnsub){tplUnsub();tplUnsub=null;}trips=[];}
  render();
});
```

**変更後:**
```js
auth.onAuthStateChanged(function(u){
  user=u;
  if(u&&isGuest){isGuest=false;trips=[];selId=null;view="list";}
  var sharedId=getSharedId();
  if(sharedId&&!isViewOnly){loadSharedTrip(sharedId);return;}
  if(u){subscribeTrips();subscribeTemplates();loadProfile();}
  else{if(tripsUnsub){tripsUnsub();tripsUnsub=null;}if(tplUnsub){tplUnsub();tplUnsub=null;}trips=[];}
  render();
});
```

- [ ] **Step 2: ゲストモードからログインする動作を確認する**

1. 「ログインせずに試す」でゲストモードに入る
2. バナーの「ログイン」ボタンでログイン画面に戻る
3. Googleログインを行う
4. デモデータが消え、自分のFirestoreデータが表示されることを確認

- [ ] **Step 3: git push してデプロイする**

```bash
git push origin main
```

GitHub Pagesの反映を待ち（約1〜2分）、https://ylee0510.github.io/tavy/ でゲストモードが動作することを確認する。
