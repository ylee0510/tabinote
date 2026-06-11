# 旅行カード編集・地域タグ付け・絞り込み Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 旅行に国/都道府県を複数選択で付与し、旅行名・目的地等を編集できるようにして、トップページ（自分の旅行・タイムライン）を地域で絞り込めるようにする。

**Architecture:** 既存の単一 `index.html`（バニラ JS / `ce`・`ap`・`tx` の手動 DOM 構築 + グローバル状態 + `render()` / Firestore）に追記する。`trips`・`feed` に `regions: string[]`（正規化済み日本語名）を追加。大陸/地方でグループ化した静的マスタからアコーディオン式ピッカーを構築し、作成・編集モーダルで使う。フィルタは「自分の旅行」はクライアント側、「タイムライン」は Firestore 再クエリ。

**Tech Stack:** Vanilla JS（ES5 風）、Firebase Firestore v8 compat、Leaflet（無関係）。ビルド無し。

> **テストについて:** 本リポジトリにはテストランナー・package.json が無い（単一 `index.html`）。そのため各タスクの「検証」は preview ツール（`preview_start` / `preview_eval` / `preview_snapshot` / `preview_screenshot` / `preview_console_logs`）による手動フロー確認に置き換える。コミットは各タスク完了時に行う。

---

## File Structure

すべて `index.html` 内の編集。論理的な追加位置:

- **静的マスタ + 派生ルックアップ + ヘルパ**: `flagEmoji`（582 行付近）の直後に追加。
- **地域ピッカー部品** `renderRegionPicker`: モーダル群の近く（`mkOverlay` 1500 行付近の手前）に追加。
- **状態変数**: `tripForm`(544)・`showNewTrip`等(550)・`listMode`(562) 付近に追加。
- **作成モーダル** `renderModal_newTrip`(1504): 拡張。
- **編集モーダル** `renderModal_editTrip`: 新規。`render()` のモーダル描画箇所(983 付近)に登録。
- **`createTrip`**(608) / **`syncFeed`**(679) / **`loadFeed`**(783) / **`switchListMode`**(811): 拡張。
- **`renderList`**(1112) / **`renderDetail`**(1287) / **`renderFeedCard`**(1177): 地域表示 + フィルタ UI。
- **CSS**: `<style>` 内に地域チップ/アコーディオン用クラスを追加。
- **ドキュメント**: `docs/firestore-feed-rules.md` に複合インデックス追記。

---

## Task 1: 地域マスタとヘルパを追加

**Files:**
- Modify: `index.html`（`flagEmoji` 定義の直後、582 行付近）

- [ ] **Step 1: マスタと派生ルックアップ・ヘルパを追加**

`flagEmoji(...)` の行の直後に以下を挿入する。

```javascript
// ===== 地域マスタ =====
var COUNTRIES_BY_CONTINENT=[
  ["アジア",[["韓国","KR"],["台湾","TW"],["中国","CN"],["香港","HK"],["マカオ","MO"],["タイ","TH"],["ベトナム","VN"],["シンガポール","SG"],["マレーシア","MY"],["インドネシア","ID"],["フィリピン","PH"],["カンボジア","KH"],["ラオス","LA"],["ミャンマー","MM"],["インド","IN"],["スリランカ","LK"],["ネパール","NP"],["モンゴル","MN"],["ブータン","BT"],["バングラデシュ","BD"]]],
  ["ヨーロッパ",[["フランス","FR"],["イタリア","IT"],["スペイン","ES"],["ドイツ","DE"],["イギリス","GB"],["スイス","CH"],["オーストリア","AT"],["オランダ","NL"],["ベルギー","BE"],["ポルトガル","PT"],["ギリシャ","GR"],["チェコ","CZ"],["ハンガリー","HU"],["ポーランド","PL"],["クロアチア","HR"],["アイルランド","IE"],["デンマーク","DK"],["スウェーデン","SE"],["ノルウェー","NO"],["フィンランド","FI"],["アイスランド","IS"],["ロシア","RU"],["トルコ","TR"]]],
  ["北米・カリブ海地域",[["アメリカ","US"],["カナダ","CA"],["グアム","GU"],["キューバ","CU"],["ジャマイカ","JM"],["バハマ","BS"],["ドミニカ共和国","DO"],["プエルトリコ","PR"]]],
  ["中南米",[["メキシコ","MX"],["ブラジル","BR"],["ペルー","PE"],["アルゼンチン","AR"],["チリ","CL"],["コロンビア","CO"],["ボリビア","BO"],["エクアドル","EC"],["グアテマラ","GT"],["コスタリカ","CR"]]],
  ["オセアニア",[["オーストラリア","AU"],["ニュージーランド","NZ"],["フィジー","FJ"],["パラオ","PW"],["タヒチ","PF"],["ニューカレドニア","NC"]]],
  ["中東",[["アラブ首長国連邦","AE"],["カタール","QA"],["イスラエル","IL"],["ヨルダン","JO"],["サウジアラビア","SA"],["オマーン","OM"],["バーレーン","BH"],["クウェート","KW"]]],
  ["アフリカ",[["エジプト","EG"],["モロッコ","MA"],["南アフリカ","ZA"],["ケニア","KE"],["タンザニア","TZ"],["チュニジア","TN"],["エチオピア","ET"],["モーリシャス","MU"]]]
];
var PREFS_BY_REGION=[
  ["北海道・東北",["北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県"]],
  ["関東",["茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県"]],
  ["中部",["新潟県","富山県","石川県","福井県","山梨県","長野県","岐阜県","静岡県","愛知県"]],
  ["近畿",["三重県","滋賀県","京都府","大阪府","兵庫県","奈良県","和歌山県"]],
  ["中国",["鳥取県","島根県","岡山県","広島県","山口県"]],
  ["四国",["徳島県","香川県","愛媛県","高知県"]],
  ["九州・沖縄",["福岡県","佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県","沖縄県"]]
];
// 名前 → {group, cc, mode}
var REGION_INDEX=(function(){
  var idx={};
  COUNTRIES_BY_CONTINENT.forEach(function(g){g[1].forEach(function(c){idx[c[0]]={group:g[0],cc:c[1],mode:"overseas"};});});
  PREFS_BY_REGION.forEach(function(g){g[1].forEach(function(p){idx[p]={group:g[0],cc:null,mode:"domestic"};});});
  return idx;
})();
function regionGroups(mode){return mode==="domestic"?PREFS_BY_REGION:COUNTRIES_BY_CONTINENT;}
// 地域名 → 表示ラベル（国は国旗付き）。県は名前のみ。
function regionLabel(name){var info=REGION_INDEX[name];if(info&&info.cc)return flagEmoji(info.cc)+" "+name;return name;}
```

- [ ] **Step 2: 構文確認（preview 起動）**

Run: `preview_start`（または既存サーバへ `preview_eval: window.location.reload()`）
その後 `preview_console_logs` を確認。
Expected: 新規の構文エラー・参照エラーが出ないこと。`preview_eval: Object.keys(REGION_INDEX).length` が 0 より大きい（県47 + 国 約80）こと。

- [ ] **Step 3: コミット**

```bash
git add index.html
git commit -m "feat: 地域マスタ（国/都道府県）と派生ルックアップを追加"
```

---

## Task 2: 地域ピッカー部品とCSSを追加

**Files:**
- Modify: `index.html`（`<style>` 内にクラス追加 / `mkOverlay`(1500) 手前に部品追加）

- [ ] **Step 1: CSS を追加**

`<style>` 内、`.chip{...}`（121 行付近）の直後に追加する。

```css
.rp-selected{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;}
.rp-chip{display:inline-flex;align-items:center;gap:4px;background:var(--accent);color:#fff;border-radius:16px;padding:4px 10px;font-size:12px;font-weight:700;cursor:pointer;border:none;font-family:inherit;}
.rp-chip .rp-x{opacity:.8;font-weight:700;}
.rp-acc{border:1.5px solid var(--border);border-radius:10px;overflow:hidden;}
.rp-grp{border-top:1px solid var(--border);}
.rp-grp:first-child{border-top:none;}
.rp-grp-hd{display:flex;align-items:center;justify-content:space-between;padding:10px 13px;font-size:13px;font-weight:700;color:#1c1917;cursor:pointer;background:var(--paper);}
.rp-grp-hd .rp-caret{color:var(--muted);font-size:12px;}
.rp-grp-body{display:flex;flex-wrap:wrap;gap:6px;padding:10px 13px;}
.rp-opt{background:var(--stamp);border:1.5px solid var(--border);border-radius:16px;padding:5px 11px;font-size:12px;font-weight:600;color:var(--muted);cursor:pointer;font-family:inherit;}
.rp-opt.on{background:#dbeafe;border-color:#1d4ed8;color:#1d4ed8;}
.region-tag{display:inline-flex;align-items:center;gap:3px;background:var(--stamp);border-radius:8px;padding:2px 8px;font-size:11px;font-weight:600;color:var(--muted);}
.region-filter{width:100%;padding:9px 12px;border:1.5px solid var(--border);border-radius:10px;font-size:14px;color:#1c1917;background:#fff;font-family:inherit;margin:0 0 12px;}
```

- [ ] **Step 2: ピッカー部品と開閉状態を追加**

`mkOverlay`(1500 行付近) の手前に挿入する。`rpOpenGroups` は開いているグループ見出しの集合。

```javascript
var rpOpenGroups={}; // グループ名 → true（アコーディオン開閉）
// mode: "overseas"|"domestic", selected: string[], onToggle: function(name)
function renderRegionPicker(mode,selected,onToggle){
  var wrap=ce("div","");
  // 選択済みチップ
  if(selected.length){
    var sel=ce("div","rp-selected");
    selected.forEach(function(nm){
      var c=ce("button","rp-chip",{type:"button",onclick:function(){onToggle(nm);}});
      ap(c,tx(regionLabel(nm)),ap(ce("span","rp-x"),tx("×")));ap(sel,c);
    });
    ap(wrap,sel);
  }
  var acc=ce("div","rp-acc");
  regionGroups(mode).forEach(function(g){
    var gname=g[0],items=g[1];
    var open=!!rpOpenGroups[gname];
    var grp=ce("div","rp-grp");
    var hd=ce("div","rp-grp-hd",{onclick:function(){rpOpenGroups[gname]=!open;render();}});
    var cnt=items.filter(function(it){var nm=mode==="domestic"?it:it[0];return selected.indexOf(nm)>=0;}).length;
    ap(hd,tx(gname+(cnt?" ("+cnt+")":"")),ap(ce("span","rp-caret"),tx(open?"▲":"▼")));
    ap(grp,hd);
    if(open){
      var body=ce("div","rp-grp-body");
      items.forEach(function(it){
        var nm=mode==="domestic"?it:it[0];
        var on=selected.indexOf(nm)>=0;
        var b=ce("button","rp-opt"+(on?" on":""),{type:"button",onclick:function(){onToggle(nm);}});
        ap(b,tx(regionLabel(nm)));ap(body,b);
      });
      ap(grp,body);
    }
    ap(acc,grp);
  });
  ap(wrap,acc);
  return wrap;
}
// selected 配列に対するトグル（破壊的）。呼び出し側で render() する。
function toggleRegion(arr,nm){var i=arr.indexOf(nm);if(i>=0)arr.splice(i,1);else arr.push(nm);}
```

- [ ] **Step 3: 構文確認**

Run: `preview_eval: window.location.reload()` → `preview_console_logs`
Expected: エラー無し。`preview_eval: typeof renderRegionPicker` が `"function"`。

- [ ] **Step 4: コミット**

```bash
git add index.html
git commit -m "feat: 地域選択ピッカー（アコーディオン）とCSSを追加"
```

---

## Task 3: 作成モーダルとcreateTripに地域を組み込む

**Files:**
- Modify: `index.html`（`tripForm`(544) / `createTrip`(608) / `renderModal_newTrip`(1504)）

- [ ] **Step 1: tripForm に regions を追加**

544 行を変更。

```javascript
var tripForm={name:"",destination:"",startDate:"",endDate:"",type:"overseas",regions:[]};
```

- [ ] **Step 2: createTrip に regions 保存とリセットを追加**

`createTrip`(608) の `db.collection("trips").add({...})` のオブジェクトに `regions:tripForm.regions.slice(),` を `type:tripForm.type,` の直後へ追加する。さらに作成成功後の
`tripForm={name:"",destination:"",startDate:"",endDate:"",type:"overseas"};`
を次へ置き換える。

```javascript
tripForm={name:"",destination:"",startDate:"",endDate:"",type:"overseas",regions:[]};
```

- [ ] **Step 3: 作成モーダルにピッカーを追加 & 種類切替で regions クリア**

`renderModal_newTrip`(1504) 内、種類トグル生成行を次へ置き換える（切替時に regions クリア）。

```javascript
  var tr=ce("div","type-row");["domestic","overseas"].forEach(function(t){ap(tr,ap(ce("button","type-btn"+(tripForm.type===t?" on":""),{onclick:function(){if(tripForm.type!==t){tripForm.type=t;tripForm.regions=[];}render();}}),tx(t==="domestic"?"🏠 国内":"✈️ 海外")));});
```

続けて、目的地などの入力フィールド生成（`[["name",...],["destination",...]].forEach(...)` ブロック）の直後に、地域ピッカーを差し込む。

```javascript
  var rg=ce("div","fg");ap(rg,ap(ce("label","lbl"),tx(tripForm.type==="overseas"?"行き先の国（複数選択可）":"行き先の都道府県（複数選択可）")));
  ap(rg,renderRegionPicker(tripForm.type,tripForm.regions,function(nm){toggleRegion(tripForm.regions,nm);render();}));
  ap(m.modal,rg);
```

- [ ] **Step 4: 検証（preview）**

Run: `preview_eval: window.location.reload()`。ログイン状態で「＋追加」→ 新規モーダルを開く。
- `preview_snapshot` で「行き先の国（複数選択可）」ラベルとアコーディオン見出し（アジア等）が出ること。
- `preview_click` でグループ見出し（例「アジア」）→ 展開、国チップが出る。
- 国チップを2つクリック → 上部に選択チップが2つ出る。
- 種類トグルを「国内」に切替 → 選択がクリアされ、都道府県の地方見出しに変わる。
- `preview_screenshot` を取得。

- [ ] **Step 5: コミット**

```bash
git add index.html
git commit -m "feat: 旅行作成時に国/都道府県を複数選択できるようにする"
```

---

## Task 4: 編集モーダルと編集ボタンを追加

**Files:**
- Modify: `index.html`（状態変数(550) / `render()` モーダル描画(983 付近) / 新規 `renderModal_editTrip` / `renderDetail`(1287)）

- [ ] **Step 1: 編集用の状態変数を追加**

550 行の `var showNewTrip=false,...` に `showEditTrip` を追加し、直後に `editDraft` を宣言する。550 行を次へ置き換える。

```javascript
var showNewTrip=false,showEditTrip=false,showShare=false,showPinModal=false,showMap=false,showNewBudget=false,showGuide=false,showMenu=false,showMyPage=false,guidePage="guide";
var editDraft=null;
```

- [ ] **Step 2: 編集モーダル関数を追加**

`renderModal_newTrip`(1504) の関数定義の直後（`}` の後）に追加する。

```javascript
function openEditTrip(){
  var sel=getSel();if(!sel)return;
  editDraft={name:sel.name||"",destination:sel.destination||"",startDate:sel.startDate||"",endDate:sel.endDate||"",type:sel.type||"overseas",regions:(sel.regions||[]).slice()};
  showEditTrip=true;render();
}
async function saveEditTrip(){
  if(!editDraft||!editDraft.name.trim())return;
  await upd({name:editDraft.name.trim(),destination:editDraft.destination.trim(),startDate:editDraft.startDate,endDate:editDraft.endDate,type:editDraft.type,regions:editDraft.regions.slice()});
  showEditTrip=false;editDraft=null;toast("保存しました");render();
}
function renderModal_editTrip(){
  if(!editDraft)return ce("div","");
  var m=mkOverlay(function(){showEditTrip=false;editDraft=null;render();});
  ap(m.modal,ap(ce("div","modal-title"),tx("✏️ 旅行を編集")));
  var tg=ce("div","fg");ap(tg,ap(ce("label","lbl"),tx("旅行の種類")));
  var tr=ce("div","type-row");["domestic","overseas"].forEach(function(t){ap(tr,ap(ce("button","type-btn"+(editDraft.type===t?" on":""),{onclick:function(){if(editDraft.type!==t){editDraft.type=t;editDraft.regions=[];}render();}}),tx(t==="domestic"?"🏠 国内":"✈️ 海外")));});
  ap(tg,tr);ap(m.modal,tg);
  [["name","旅行名 *","例：夏の韓国旅行"],["destination","行き先","例：ソウル・釜山"]].forEach(function(f){
    var g=ce("div","fg");ap(g,ap(ce("label","lbl"),tx(f[1])));var inp=ce("input","finp",{type:"text",placeholder:f[2],value:editDraft[f[0]],oninput:function(e){editDraft[f[0]]=e.target.value;}});ap(g,inp);ap(m.modal,g);
  });
  var dr=ce("div","",{style:{display:"flex",gap:"10px",marginBottom:"11px"}});
  [["startDate","出発日"],["endDate","帰着日"]].forEach(function(f){var g=ce("div","",{style:{flex:"1"}});ap(g,ap(ce("label","lbl"),tx(f[1])),ce("input","finp",{type:"date",value:editDraft[f[0]],oninput:function(e){editDraft[f[0]]=e.target.value;}}));ap(dr,g);});
  ap(m.modal,dr);
  var rg=ce("div","fg");ap(rg,ap(ce("label","lbl"),tx(editDraft.type==="overseas"?"行き先の国（複数選択可）":"行き先の都道府県（複数選択可）")));
  ap(rg,renderRegionPicker(editDraft.type,editDraft.regions,function(nm){toggleRegion(editDraft.regions,nm);render();}));
  ap(m.modal,rg);
  var b=ce("button","btn-ok",{onclick:saveEditTrip});ap(b,tx("保存する"));
  ap(m.modal,ap(ce("div","modal-acts"),ap(ce("button","btn-cancel",{onclick:function(){showEditTrip=false;editDraft=null;render();}}),tx("キャンセル")),b));
  return m.ov;
}
```

- [ ] **Step 3: render() にモーダル登録**

`render()` 内の `if(showNewTrip)ap(wrap,renderModal_newTrip());`（983 行付近）の直後に追加する。

```javascript
  if(showEditTrip)ap(wrap,renderModal_editTrip());
```

- [ ] **Step 4: 詳細ヒーローに編集ボタンを追加**

`renderDetail`(1287) 内、`ap(hero,hm);ap(wrap,hero);`（1305 行付近）の直前に、オーナー限定の編集ボタンを hero へ追加する。`ap(hero,hm);` を次へ置き換える。

```javascript
  if(!isViewOnly&&!isGuest&&user&&sel.ownerId===user.uid){
    var edBtn=ce("button","hero-cover-btn",{style:{right:"auto",left:"12px"},onclick:openEditTrip});
    edBtn.style.display="inline-flex";edBtn.style.alignItems="center";edBtn.style.gap="5px";ap(edBtn,tx("✏️ 編集"));ap(covW,edBtn);
  }
  ap(hero,hm);
```

（注: `hero-cover-btn` は既存のカバー変更ボタンと同じ右下配置クラス。`left` 指定で左下へずらす。重なりが気になる場合は Step 6 で位置調整。）

- [ ] **Step 5: 検証（preview）**

Run: `preview_eval: window.location.reload()`。自分の旅行を1つ開く（詳細）。
- `preview_snapshot` で「✏️ 編集」ボタンが見えること。
- `preview_click` で編集 → モーダルに現在の旅行名・目的地・日付・地域が反映されていること。
- 旅行名を変更し「保存する」→ ヘッダ/詳細に反映、「保存しました」トースト。
- `preview_screenshot` を取得。

- [ ] **Step 6: 必要ならボタン位置を微調整しコミット**

カバー変更ボタンと編集ボタンが重なる場合のみ、`hero-cover-btn` の配置を調整（例: 編集ボタンに `bottom:auto;top:12px`）。問題なければそのまま。

```bash
git add index.html
git commit -m "feat: 旅行名・目的地・日付・地域を編集できる編集モーダルを追加"
```

---

## Task 5: カード・詳細・フィードに地域を表示

**Files:**
- Modify: `index.html`（`renderList`(1150 付近) / `renderDetail`(1302) / `renderFeedCard`(1177 付近)）

- [ ] **Step 1: 自分の旅行カードに地域タグを表示**

`renderList`(1112) の「行2: 目的地」ブロック（1154-1157 行付近）を次へ置き換える。`regions` があればタグ列、続けて `destination` テキスト。

```javascript
    // 行2: 地域タグ + 目的地
    var row2=ce("div","",{style:{display:"flex",flexWrap:"wrap",gap:"6px",alignItems:"center",marginBottom:"4px",minHeight:"18px"}});
    (trip.regions||[]).forEach(function(rn){ap(row2,ap(ce("span","region-tag"),tx(regionLabel(rn))));});
    if(trip.destination){var dt=ce("span","",{style:{fontSize:"13px",color:"var(--muted)",display:"inline-flex",alignItems:"center",gap:"4px"}});ap(dt,svgIcon("pin","currentColor",13),tx(trip.destination));ap(row2,dt);}
    ap(body,row2);
```

- [ ] **Step 2: 詳細ヒーローに地域タグを表示**

`renderDetail`(1287) の `if(sel.destination)ap(hm,ap(ce("span",""),tx(" "+sel.destination)));`（1302 行）を次へ置き換える。

```javascript
  if(sel.regions&&sel.regions.length){var rgw=ce("span","",{style:{display:"inline-flex",flexWrap:"wrap",gap:"5px"}});sel.regions.forEach(function(rn){ap(rgw,ap(ce("span","region-tag"),tx(regionLabel(rn))));});ap(hm,rgw);}
  if(sel.destination)ap(hm,ap(ce("span",""),tx(" "+sel.destination)));
```

- [ ] **Step 3: フィードカードに地域タグを表示**

`renderFeedCard`(1177) 内、`feed-card-title` を表示している箇所を特定する（`item.name` を出している行）。その直後に地域タグ列を追加する。まず該当箇所を確認:

Run: `grep -n "feed-card-title\|item.destination" index.html`

`feed-card-title` の div を本文へ `ap` している行の直後に、以下を挿入する（`bodyWrap` 等の本文コンテナ変数名は周辺コードに合わせる）。

```javascript
    if(item.regions&&item.regions.length){var frg=ce("div","",{style:{display:"flex",flexWrap:"wrap",gap:"5px",marginTop:"4px"}});item.regions.forEach(function(rn){ap(frg,ap(ce("span","region-tag"),tx(regionLabel(rn))));});ap(<本文コンテナ>,frg);}
```

（`<本文コンテナ>` は実際の変数名に置換。例えば本文 div が `b` なら `ap(b,frg)`。）

- [ ] **Step 4: 検証（preview）**

Run: `preview_eval: window.location.reload()`。
- 自分の旅行一覧で、地域を付けた旅行カードに国旗付きタグが出ること（`preview_snapshot`）。
- 詳細ヒーローにタグが出ること。
- タイムラインに公開済み（regions 付き）があればフィードカードにもタグ。無ければ Task 6 後に再確認。
- `preview_screenshot` を取得。

- [ ] **Step 5: コミット**

```bash
git add index.html
git commit -m "feat: カード・詳細・フィードに地域タグを表示"
```

---

## Task 6: フィード同期に regions を追加

**Files:**
- Modify: `index.html`（`syncFeed`(679)）

- [ ] **Step 1: syncFeed の meta に regions を追加**

`syncFeed`(685-697) の `meta` オブジェクト内、`type:trip.type||"overseas",` の直後に追加する。

```javascript
    regions:trip.regions||[],
```

- [ ] **Step 2: 検証（preview）**

Run: `preview_eval: window.location.reload()`。地域を付けた自分の旅行を公開（共有モーダルから公開）し、`feed` に反映後、タイムラインのフィードカードに地域タグが出ること（`preview_snapshot`）。`preview_console_logs` でエラー無し。

- [ ] **Step 3: コミット**

```bash
git add index.html
git commit -m "feat: フィード公開データに regions を同期"
```

---

## Task 7: 地域フィルタ（自分の旅行・タイムライン）

**Files:**
- Modify: `index.html`（状態変数(562 付近) / `loadFeed`(783) / `switchListMode`(811) / `renderList`(1112)）

- [ ] **Step 1: フィルタ状態を追加**

562 行 `var listMode="mine";` の直後に追加する。

```javascript
var mineRegionFilter="",tlRegionFilter="";
```

- [ ] **Step 2: loadFeed を地域フィルタ対応に**

`loadFeed`(783) のクエリ生成行 `var q=db.collection("feed").orderBy("publishedAt","desc").limit(30);` を次へ置き換える。

```javascript
    var q=db.collection("feed");
    if(tlRegionFilter)q=q.where("regions","array-contains",tlRegionFilter);
    q=q.orderBy("publishedAt","desc").limit(30);
```

- [ ] **Step 3: 地域変更で再クエリする関数を追加**

`switchListMode`(811) 関数の直後に追加する。

```javascript
function setTlRegionFilter(v){tlRegionFilter=v;loadFeed(true);}
function setMineRegionFilter(v){mineRegionFilter=v;render();}
// グループ化した地域 select を作る。groupsSource: [[group,[name...]],...]、availableSet: 表示する名前のSet（null なら全部）
function renderRegionSelect(value,onChange,availableSet){
  var sel=ce("select","region-filter",{onchange:function(e){onChange(e.target.value);}});
  var allOpt=ce("option","",{value:""});ap(allOpt,tx("🗺️ すべての地域"));ap(sel,allOpt);
  [["国",COUNTRIES_BY_CONTINENT,"overseas"],["国内",PREFS_BY_REGION,"domestic"]].forEach(function(){});
  function addGroups(groups,mode){
    groups.forEach(function(g){
      var names=g[1].map(function(it){return mode==="domestic"?it:it[0];}).filter(function(nm){return !availableSet||availableSet.has(nm);});
      if(!names.length)return;
      var og=ce("optgroup","",{label:g[0]});
      names.forEach(function(nm){var o=ce("option","",{value:nm});if(nm===value)o.selected=true;ap(o,tx(regionLabel(nm)));ap(og,o);});
      ap(sel,og);
    });
  }
  addGroups(COUNTRIES_BY_CONTINENT,"overseas");
  addGroups(PREFS_BY_REGION,"domestic");
  return sel;
}
```

（注: 中段の no-op `forEach` 行は不要なら削除可。`addGroups` が本体。）

- [ ] **Step 4: renderList にフィルタ UI と「自分の旅行」フィルタ適用**

`renderList`(1112) のセグメント追加 `ap(seg,t1,t2);ap(outer,seg);`（1117 行）の直後に、モードごとのフィルタ select を追加する。

```javascript
  if(listMode==="timeline"){
    ap(outer,renderRegionSelect(tlRegionFilter,setTlRegionFilter,null));
  }else{
    var avail=new Set();trips.forEach(function(t){(t.regions||[]).forEach(function(r){avail.add(r);});});
    if(avail.size)ap(outer,renderRegionSelect(mineRegionFilter,setMineRegionFilter,avail));
  }
```

次に「自分の旅行」一覧のループ対象をフィルタ適用したリストへ変更する。`renderList` 内 `trips.forEach(function(trip){`（1135 行付近）を次へ置き換える。

```javascript
  var mineList=mineRegionFilter?trips.filter(function(t){return (t.regions||[]).indexOf(mineRegionFilter)>=0;}):trips;
  mineList.forEach(function(trip){
```

（注: ループ内で `trips` を参照している箇所があれば `mineList` には変えず、`trip` 変数のみ使用していることを確認。空配列ガード `if(trips.length===0)` は既存のまま温存。）

- [ ] **Step 5: 検証（preview）**

Run: `preview_eval: window.location.reload()`。
- 「自分の旅行」: 地域を付けた旅行が複数あれば select が出る。地域を選ぶと該当のみ表示、「すべての地域」で全件（`preview_snapshot` で件数確認）。
- 「タイムライン」: select で地域を選ぶと Firestore 再クエリ。`preview_console_logs` でインデックス未作成エラー（`FAILED_PRECONDITION` / index リンク）が出たら Task 8 のインデックスを作成してから再確認。
- 「もっと見る」が同じ地域フィルタで継続ページングすること。
- `preview_screenshot` を取得。

- [ ] **Step 6: コミット**

```bash
git add index.html
git commit -m "feat: トップページを国/都道府県で絞り込めるようにする"
```

---

## Task 8: Firestore 複合インデックスを文書化

**Files:**
- Modify: `docs/firestore-feed-rules.md`

- [ ] **Step 1: 複合インデックスを追記**

`docs/firestore-feed-rules.md` の末尾に、タイムライン地域フィルタ用インデックスを追記する。

```markdown
## 複合インデックス（タイムライン地域フィルタ）

地域でタイムラインを絞り込むため、`feed` コレクションに以下の複合インデックスが必要:

- コレクション: `feed`
- フィールド: `regions`（Arrays / ARRAY_CONTAINS）, `publishedAt`（Descending）

Firestore コンソールでクエリ実行時に表示される自動作成リンクからでも作成可。`feed` ドキュメントには `syncFeed` で `regions: string[]` を保存している。
```

- [ ] **Step 2: 実インデックスの作成確認**

Task 7 のタイムラインフィルタ検証時に `FAILED_PRECONDITION` が出た場合、コンソールのリンクからインデックスを作成し、ビルド完了後に再検証する。エラーが出なければ既に存在。

- [ ] **Step 3: コミット**

```bash
git add docs/firestore-feed-rules.md
git commit -m "docs: タイムライン地域フィルタ用の複合インデックスを記録"
```

---

## Task 9: 全体フロー検証

- [ ] **Step 1: エンドツーエンド確認（preview）**

Run: `preview_eval: window.location.reload()`。以下を順に確認し、`preview_console_logs` でエラーが無いこと:
1. 新規作成（海外）で国を2つ選択 → カード/詳細に国旗タグ。
2. 新規作成（国内）で都道府県を2つ選択 → タグ表示。
3. 既存旅行を編集 → 旅行名・目的地・日付・地域を変更 → 反映。
4. 編集で種類を切替 → regions クリア。
5. 「自分の旅行」フィルタ → 該当のみ / 解除で全件。
6. 旅行を公開 → タイムラインにタグ表示 → タイムライン地域フィルタで該当公開旅行が出る → 「もっと見る」継続。

- [ ] **Step 2: 最終スクリーンショット**

Run: `preview_screenshot`（一覧・詳細・編集モーダル各 1 枚）。ユーザーへ提示。

---

## Self-Review 結果

- **スペック網羅**: 編集（Task 4）/ 作成時複数選択（Task 1-3）/ 絞り込み 自分の旅行（Task 7）/ タイムライン再クエリ（Task 6,7,8）/ 両方持つデータモデル（Task 3,4）/ 表示（Task 5）/ インデックス（Task 8）— すべて対応。
- **プレースホルダ**: Task 5 Step 3 の `<本文コンテナ>` のみ実コード参照が必要（フィードカードの本文変数名）。実行時に `grep` で確認する手順を明記済み。
- **型一貫性**: `regions` は全タスクで `string[]`。`renderRegionPicker(mode,selected,onToggle)` / `toggleRegion(arr,nm)` / `regionLabel(name)` のシグネチャは Task 2 定義と Task 3,4,5,7 の呼び出しで一致。
