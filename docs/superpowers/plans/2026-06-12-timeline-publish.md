# タイムラインへの投稿機能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 旅行詳細画面の「自分の旅行 / タイムライン」セグメントの右側に「投稿」ボタンを追加し、専用モーダルからタイムライン公開設定（公開タブ選択・投稿・更新・停止）を行えるようにする。同じ設定を旅行編集モーダルの末尾からも操作できるようにし、既存の共有モーダルからは公開セクションを削除する。

**Architecture:** 既存の単一 `index.html`（バニラ JS / `ce`・`ap`・`tx` の手動 DOM 構築 + グローバル状態 + `render()` / Firestore）に追記する。共有モーダル内にあった「みんなのタイムラインに公開」ロジックを `renderPublishSection(withHeading)` という共通パーツに抽出し、新規の `renderModal_publish()`（投稿モーダル、状態 `showPublish`）と既存の `renderModal_editTrip()` の両方から呼び出す。`renderListSeg()` を `renderListSeg(trailing)` に拡張し、`renderDetail()` から「投稿」/「公開中」ボタン（globe / check の `svgIcon`）を渡す。絵文字は使わず、既存の `ICONS`（`globe`, `check`）のみを使用する。

**Tech Stack:** Vanilla JS（ES5 風）、Firebase Firestore v8 compat。ビルド無し。Firestore スキーマ変更・新規アイコン追加なし。

> **テストについて:** 本リポジトリにはテストランナー・package.json が無い（単一 `index.html`）。そのため各タスクの「検証」は preview ツール（`preview_start` / `preview_eval` / `preview_snapshot` / `preview_screenshot` / `preview_console_logs`）による手動フロー確認に置き換える。コミットは各タスク完了時に行う。

---

## File Structure

すべて `index.html` 内の編集。論理的な追加・変更位置:

- **状態変数**: `showShare`(589 行付近) の並びに `showPublish` を追加。
- **共通公開セクション** `renderPublishSection(withHeading)`・**投稿モーダル** `renderModal_publish()`: `renderPublishTabPicker()`(1781〜1792 行) の直後、`renderModal_share()`(1793 行) の手前に新規追加。
- **共有モーダル** `renderModal_share()`: 「みんなのタイムラインに公開」ブロックを削除。
- **モーダル分岐** `render()`(1099 行付近): `if(showPublish)ap(wrap,renderModal_publish());` を追加。
- **CSS**: `.feed-seg`(76 行) に `align-items:center` 追加 + `.feed-seg-post` / `.feed-seg-post.published` を新規追加。
- **`renderListSeg`**(1230 行): `trailing` 引数を追加。
- **`renderDetail`**(1435〜1437 行): 投稿/公開中ボタンを生成して `renderListSeg` に渡す。
- **`openEditTrip`**(1750 行) / **`saveEditTrip`**(1755 行) / **`renderModal_editTrip`**(1760 行): `publishDraftTabs` のリセットと `renderPublishSection(true)` の挿入。
- **ガイド配列**(2176〜2183 行付近): 新項目「タイムラインに投稿する」を追加。

参考: 設計仕様は `docs/superpowers/specs/2026-06-12-timeline-publish-design.md`（コミット済み・未push）。

---

## Task 1: 投稿モーダルと共通公開セクションの新規作成・共有モーダルの整理

**Files:**
- Modify: `index.html`（589 行 / 1099 行 / 1781〜1833 行）

- [ ] **Step 1: `showPublish` 状態変数を追加**

589 行目を変更する。

Before:
```javascript
var showNewTrip=false,showEditTrip=false,showShare=false,showPinModal=false,showMap=false,showNewBudget=false,showGuide=false,showMenu=false,showMyPage=false,guidePage="guide";
```

After:
```javascript
var showNewTrip=false,showEditTrip=false,showShare=false,showPublish=false,showPinModal=false,showMap=false,showNewBudget=false,showGuide=false,showMenu=false,showMyPage=false,guidePage="guide";
```

- [ ] **Step 2: `renderPublishSection(withHeading)` と `renderModal_publish()` を追加**

`renderPublishTabPicker(){...}` の関数定義（1792 行の `}`）の直後、`function renderModal_share(){` の手前に以下を挿入する。

```javascript
// タイムライン公開設定の共通UI（投稿モーダル・編集モーダルで共有）
// withHeading=true の場合、先頭に見出し「タイムラインに公開」を表示する（編集モーダル用）
function renderPublishSection(withHeading){
  var sel=getSel();if(!sel)return ce("div","");
  var box=ce("div","");
  if(withHeading){
    ap(box,ap(ce("div","",{style:{fontSize:"12px",fontWeight:"700",color:"var(--muted)",margin:"4px 0 8px",textTransform:"uppercase",letterSpacing:"1px"}}),tx("タイムラインに公開")));
  }
  if(publishDraftTabs==null)publishDraftTabs=(sel.publicTabs||["itinerary"]).slice();
  if(sel.publishedToFeed){
    var st=ce("div","",{style:{fontSize:"13px",color:"var(--green)",fontWeight:"700",marginBottom:"8px",display:"flex",alignItems:"center",gap:"6px"}});
    ap(st,svgIcon("check","var(--green)",14),tx("タイムラインに公開中"));ap(box,st);
    ap(box,renderPublishTabPicker());
    ap(box,ap(ce("button","btn-ok",{style:{width:"100%",border:"none",marginBottom:"8px"},onclick:async function(){var tabs=publishDraftTabs.slice();await upd({publicTabs:tabs});var t=Object.assign({},getSel(),{publicTabs:tabs});await syncFeed(t);publishDraftTabs=null;toast("公開内容を更新しました");render();}}),tx("公開内容を更新する")));
    ap(box,ap(ce("button","",{style:{width:"100%",padding:"10px",background:"none",border:"1px solid var(--border)",borderRadius:"10px",fontSize:"13px",color:"var(--muted)",cursor:"pointer"},onclick:async function(){await unpublishFeed(sel.id);await upd({publishedToFeed:false});publishDraftTabs=null;toast("タイムラインへの公開を停止しました");render();}}),tx("公開を停止する")));
  }else{
    ap(box,ap(ce("div","",{style:{fontSize:"13px",color:"var(--muted)",marginBottom:"10px",lineHeight:"1.6"}}),tx("投稿すると、行程など選んだ内容がタイムラインに流れ、他のユーザーがいいね・コメントできます。")));
    ap(box,renderPublishTabPicker());
    ap(box,ap(ce("button","btn-ok",{style:{width:"100%",border:"none"},onclick:async function(){if(!(await ensureNickname())){render();return;}var tabs=publishDraftTabs.slice();await upd({publishedToFeed:true,publicTabs:tabs});var t=Object.assign({},getSel(),{publishedToFeed:true,publicTabs:tabs});await syncFeed(t);publishDraftTabs=null;track('feed_publish',{});toast("タイムラインに投稿しました！");render();}}),tx("投稿する")));
  }
  return box;
}
function renderModal_publish(){
  var sel=getSel();if(!sel)return ce("div","");
  var m=mkOverlay(function(){showPublish=false;publishDraftTabs=null;render();});
  ap(m.modal,ap(ce("div","modal-title",{style:{display:"flex",alignItems:"center",gap:"8px"}}),svgIcon("globe","currentColor",18),tx("タイムラインに投稿")));
  ap(m.modal,renderPublishSection(false));
  ap(m.modal,ap(ce("div","modal-acts"),ap(ce("button","btn-cancel",{style:{flex:"1"},onclick:function(){showPublish=false;publishDraftTabs=null;render();}}),tx("閉じる"))));
  return m.ov;
}
```

- [ ] **Step 3: `renderModal_share()` から「みんなのタイムラインに公開」ブロックを削除**

`renderModal_share()` 内の以下のブロック（リンク共有セクションとメンバー招待セクションの間にある `if(user&&sel.ownerId===user.uid){...}`）を丸ごと削除する。

Before（削除対象）:
```javascript
  if(user&&sel.ownerId===user.uid){
    ap(m.modal,ap(ce("div","",{style:{fontSize:"12px",fontWeight:"700",color:"var(--muted)",margin:"4px 0 8px",textTransform:"uppercase",letterSpacing:"1px"}}),tx("みんなのタイムラインに公開")));
    if(sel.publishedToFeed){
      ap(m.modal,ap(ce("div","",{style:{fontSize:"13px",color:"var(--green)",fontWeight:"700",marginBottom:"8px"}}),tx("✓ タイムラインに公開中")));
      if(publishDraftTabs==null)publishDraftTabs=(sel.publicTabs||["itinerary"]).slice();
      ap(m.modal,renderPublishTabPicker());
      ap(m.modal,ap(ce("button","btn-ok",{style:{width:"100%",border:"none",marginBottom:"8px"},onclick:async function(){var tabs=publishDraftTabs.slice();await upd({publicTabs:tabs});var t=Object.assign({},getSel(),{publicTabs:tabs});await syncFeed(t);publishDraftTabs=null;toast("公開内容を更新しました");render();}}),tx("公開内容を更新する")));
      ap(m.modal,ap(ce("button","",{style:{width:"100%",padding:"10px",background:"none",border:"1px solid var(--border)",borderRadius:"10px",fontSize:"13px",color:"var(--muted)",cursor:"pointer",marginBottom:"16px"},onclick:async function(){await unpublishFeed(sel.id);await upd({publishedToFeed:false});publishDraftTabs=null;toast("タイムラインへの公開を停止しました");render();}}),tx("公開を停止する")));
    }else{
      ap(m.modal,ap(ce("div","",{style:{fontSize:"13px",color:"var(--muted)",marginBottom:"10px",lineHeight:"1.6"}}),tx("公開すると、行程など選んだ内容がタイムラインに流れ、他のユーザーがいいね・コメントできます。")));
      if(publishDraftTabs==null)publishDraftTabs=(sel.publicTabs||["itinerary"]).slice();
      ap(m.modal,renderPublishTabPicker());
      ap(m.modal,ap(ce("button","btn-ok",{style:{width:"100%",border:"none",marginBottom:"16px"},onclick:async function(){if(!(await ensureNickname())){render();return;}var tabs=publishDraftTabs.slice();await upd({publishedToFeed:true,publicTabs:tabs});var t=Object.assign({},getSel(),{publishedToFeed:true,publicTabs:tabs});await syncFeed(t);publishDraftTabs=null;track('feed_publish',{});toast("タイムラインに公開しました！");render();}}),tx("タイムラインに公開する")));
    }
  }
```

After: 上記ブロックを削除し、直前のリンク共有セクション（`if(sel.isPublic){...}else{...}`）の直後に、直後の「メンバー招待」見出し（`ap(m.modal,ap(ce("div","",{style:{...}}),tx("メンバー招待（ログイン必須・編集可能）")));`）が続く形にする。

- [ ] **Step 4: `render()` のモーダル分岐に投稿モーダルを追加**

1099 行付近を変更する。

Before:
```javascript
  if(showEditTrip)ap(wrap,renderModal_editTrip());
  if(showShare)ap(wrap,renderModal_share());
```

After:
```javascript
  if(showEditTrip)ap(wrap,renderModal_editTrip());
  if(showShare)ap(wrap,renderModal_share());
  if(showPublish)ap(wrap,renderModal_publish());
```

- [ ] **Step 5: 構文確認（preview）**

Run: `preview_start`（既存サーバが動いていれば `preview_eval: window.location.reload()`）。
その後 `preview_console_logs`（level "error"）を確認。
Expected: 新規の構文エラー・参照エラーが出ないこと。この時点では「投稿」ボタンや編集モーダルからの導線はまだ無いため、UI上の見た目は変化しない（共有モーダルの「みんなのタイムラインに公開」セクションが消えていることのみ確認）。

- [ ] **Step 6: コミット**

```bash
git add index.html
git commit -m "feat: タイムライン公開設定を共通パーツ化し投稿モーダルを新規追加"
```

---

## Task 2: 詳細画面に「投稿」/「公開中」ボタンを追加

**Files:**
- Modify: `index.html`（76〜79 行 / 1230〜1240 行 / 1435〜1437 行）

- [ ] **Step 1: CSS を追加・修正**

76〜79 行を変更する。

Before:
```css
.feed-seg{display:flex;gap:22px;padding:6px 16px 0;border-bottom:1px solid var(--border);margin-bottom:14px;}
.feed-seg-tab{font-size:15px;font-weight:800;padding:8px 2px 11px;color:var(--muted);position:relative;cursor:pointer;}
.feed-seg-tab.on{color:var(--ink);}
.feed-seg-tab.on::after{content:'';position:absolute;left:0;right:0;bottom:-1px;height:2.5px;background:var(--accent);border-radius:2px;}
```

After:
```css
.feed-seg{display:flex;align-items:center;gap:22px;padding:6px 16px 0;border-bottom:1px solid var(--border);margin-bottom:14px;}
.feed-seg-tab{font-size:15px;font-weight:800;padding:8px 2px 11px;color:var(--muted);position:relative;cursor:pointer;}
.feed-seg-tab.on{color:var(--ink);}
.feed-seg-tab.on::after{content:'';position:absolute;left:0;right:0;bottom:-1px;height:2.5px;background:var(--accent);border-radius:2px;}
.feed-seg-post{margin-left:auto;margin-bottom:8px;display:inline-flex;align-items:center;gap:6px;padding:7px 14px;border-radius:20px;border:1.5px solid var(--border);background:#fff;font-size:13px;font-weight:700;color:var(--muted);cursor:pointer;font-family:inherit;}
.feed-seg-post.published{border-color:var(--green);color:var(--green);}
```

- [ ] **Step 2: `renderListSeg` に `trailing` 引数を追加**

1230〜1240 行を変更する。

Before:
```javascript
function renderListSeg(){
  var seg=ce("div","feed-seg");
  var mk=function(mode,label){
    var t=ce("div","feed-seg-tab"+(listMode===mode?" on":""),{onclick:function(){
      if(view!=="list"){view="list";selId=null;destroyMap();showMap=false;activeTab="itinerary";}
      switchListMode(mode);
    }});ap(t,tx(label));return t;
  };
  ap(seg,mk("mine","自分の旅行"),mk("timeline","タイムライン"));
  return seg;
}
```

After:
```javascript
function renderListSeg(trailing){
  var seg=ce("div","feed-seg");
  var mk=function(mode,label){
    var t=ce("div","feed-seg-tab"+(listMode===mode?" on":""),{onclick:function(){
      if(view!=="list"){view="list";selId=null;destroyMap();showMap=false;activeTab="itinerary";}
      switchListMode(mode);
    }});ap(t,tx(label));return t;
  };
  ap(seg,mk("mine","自分の旅行"),mk("timeline","タイムライン"));
  if(trailing)ap(seg,trailing);
  return seg;
}
```

`renderList()`（1241〜1243 行）は `ap(outer,renderListSeg());` のまま、変更不要（`trailing` が `undefined` の場合 `if(trailing)` が false になるため安全）。

- [ ] **Step 3: `renderDetail()` で「投稿」/「公開中」ボタンを生成して渡す**

1435〜1437 行を変更する。

Before:
```javascript
function renderDetail(){
  var sel=getSel();if(!sel)return ce("div","");var wrap=ce("div","");
  if(!isViewOnly)ap(wrap,renderListSeg());
```

After:
```javascript
function renderDetail(){
  var sel=getSel();if(!sel)return ce("div","");var wrap=ce("div","");
  if(!isViewOnly){
    var postBtn=null;
    if(!isGuest&&user&&sel.ownerId===user.uid){
      if(sel.publishedToFeed){
        postBtn=ce("button","feed-seg-post published",{onclick:function(){publishDraftTabs=null;showPublish=true;render();}});
        ap(postBtn,svgIcon("check","var(--green)",14),tx("公開中"));
      }else{
        postBtn=ce("button","feed-seg-post",{onclick:function(){publishDraftTabs=null;showPublish=true;render();}});
        ap(postBtn,svgIcon("globe","currentColor",14),tx("投稿"));
      }
    }
    ap(wrap,renderListSeg(postBtn));
  }
```

- [ ] **Step 4: 動作確認（preview）**

Run: `preview_eval: window.location.reload()`
1. オーナーで未公開の旅行を開く → セグメント右に globe アイコン + 「投稿」ボタンが表示される。
2. クリック → 投稿モーダルが開き、タブピッカーと「投稿する」ボタンが表示される。
3. 「投稿する」をクリック → トースト表示後、モーダル内が check アイコン + 「タイムラインに公開中」表示に切り替わり、「公開内容を更新する」「公開を停止する」ボタンが表示される。
4. モーダルを閉じる → セグメント右のボタンが check アイコン + 「公開中」（緑系）に変わっている。
5. `preview_screenshot` で詳細画面と投稿モーダルを撮影。
6. `preview_console_logs`（level "error"）でエラーが無いことを確認。

- [ ] **Step 5: コミット**

```bash
git add index.html
git commit -m "feat: 旅行詳細のタイムラインセグメントに投稿/公開中ボタンを追加"
```

---

## Task 3: 編集モーダルからタイムライン公開設定を変更可能にする

**Files:**
- Modify: `index.html`（1750〜1779 行）

- [ ] **Step 1: `openEditTrip()` で `publishDraftTabs` をリセット**

Before:
```javascript
function openEditTrip(){
  var sel=getSel();if(!sel)return;
  editDraft={name:sel.name||"",destination:sel.destination||"",startDate:sel.startDate||"",endDate:sel.endDate||"",type:sel.type||"overseas",regions:(sel.regions||[]).slice()};
  rpView=null;showEditTrip=true;render();
}
```

After:
```javascript
function openEditTrip(){
  var sel=getSel();if(!sel)return;
  editDraft={name:sel.name||"",destination:sel.destination||"",startDate:sel.startDate||"",endDate:sel.endDate||"",type:sel.type||"overseas",regions:(sel.regions||[]).slice()};
  publishDraftTabs=null;rpView=null;showEditTrip=true;render();
}
```

- [ ] **Step 2: `saveEditTrip()` で `publishDraftTabs` をリセット**

Before:
```javascript
async function saveEditTrip(){
  if(!editDraft||!editDraft.name.trim())return;
  await upd({name:editDraft.name.trim(),destination:editDraft.destination.trim(),startDate:editDraft.startDate,endDate:editDraft.endDate,type:editDraft.type,regions:editDraft.regions.slice()});
  showEditTrip=false;editDraft=null;toast("保存しました");render();
}
```

After:
```javascript
async function saveEditTrip(){
  if(!editDraft||!editDraft.name.trim())return;
  await upd({name:editDraft.name.trim(),destination:editDraft.destination.trim(),startDate:editDraft.startDate,endDate:editDraft.endDate,type:editDraft.type,regions:editDraft.regions.slice()});
  showEditTrip=false;editDraft=null;publishDraftTabs=null;toast("保存しました");render();
}
```

- [ ] **Step 3: `renderModal_editTrip()` に `renderPublishSection(true)` を挿入し、閉じる/キャンセル時にリセット**

Before:
```javascript
function renderModal_editTrip(){
  if(!editDraft)return ce("div","");
  var m=mkOverlay(function(){showEditTrip=false;editDraft=null;render();});
  ap(m.modal,ap(ce("div","modal-title",{style:{display:"flex",alignItems:"center",gap:"7px"}}),svgIcon("pencil","currentColor",17),tx("旅行を編集")));
  var tg=ce("div","fg");ap(tg,ap(ce("label","lbl"),tx("旅行の種類")));
  var tr=typeToggleRow(editDraft.type,function(t){if(editDraft.type!==t){editDraft.type=t;editDraft.regions=[];rpView=null;}render();});
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

After:
```javascript
function renderModal_editTrip(){
  if(!editDraft)return ce("div","");
  var m=mkOverlay(function(){showEditTrip=false;editDraft=null;publishDraftTabs=null;render();});
  ap(m.modal,ap(ce("div","modal-title",{style:{display:"flex",alignItems:"center",gap:"7px"}}),svgIcon("pencil","currentColor",17),tx("旅行を編集")));
  var tg=ce("div","fg");ap(tg,ap(ce("label","lbl"),tx("旅行の種類")));
  var tr=typeToggleRow(editDraft.type,function(t){if(editDraft.type!==t){editDraft.type=t;editDraft.regions=[];rpView=null;}render();});
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
  ap(m.modal,renderPublishSection(true));
  var b=ce("button","btn-ok",{onclick:saveEditTrip});ap(b,tx("保存する"));
  ap(m.modal,ap(ce("div","modal-acts"),ap(ce("button","btn-cancel",{onclick:function(){showEditTrip=false;editDraft=null;publishDraftTabs=null;render();}}),tx("キャンセル")),b));
  return m.ov;
}
```

- [ ] **Step 4: 動作確認（preview）**

Run: `preview_eval: window.location.reload()`
1. オーナーで旅行詳細を開き「編集」ボタン → 編集モーダルが開く。
2. 一番下（保存/キャンセルの上）に「タイムラインに公開」見出しと公開セクションが表示される（未公開なら説明文+タブピッカー+「投稿する」、公開中なら「タイムラインに公開中」+タブピッカー+「公開内容を更新する」「公開を停止する」）。
3. 編集モーダル内で「投稿する」（または「公開内容を更新する」/「公開を停止する」）をクリック → トースト表示後、即時にセクション内の表示が切り替わる（「保存する」を押さなくても反映される）。
4. 「キャンセル」または「保存する」でモーダルを閉じ、再度「編集」を開く → 公開セクションが `sel.publicTabs` の最新状態から正しく初期化されている。
5. `preview_screenshot` で編集モーダル下部を撮影。
6. `preview_console_logs`（level "error"）でエラーが無いことを確認。

- [ ] **Step 5: コミット**

```bash
git add index.html
git commit -m "feat: 旅行編集モーダルからタイムライン公開設定を変更可能にする"
```

---

## Task 4: ガイドに「タイムラインに投稿する」項目を追加

**Files:**
- Modify: `index.html`（2181〜2182 行付近）

- [ ] **Step 1: ガイド配列に新項目を挿入**

「メモを残す」の項目と「旅行を共有する」の項目の間に新しい項目を挿入する。

Before:
```javascript
   {title:"メモを残す",desc:"メモタブでは、旅する国や街の歴史・言葉・気に入ったお店などを自由に書き残せます。入力欄から離れると自動で保存され、「＋ 追加」で入力欄を増やせます。タイムラインにも公開できます。"},
   {title:"旅行を共有する",desc:"🔗ボタンから閲覧リンクを発行（ログイン不要）、またはメールアドレスで編集メンバーを招待できます。"},
```

After:
```javascript
   {title:"メモを残す",desc:"メモタブでは、旅する国や街の歴史・言葉・気に入ったお店などを自由に書き残せます。入力欄から離れると自動で保存され、「＋ 追加」で入力欄を増やせます。タイムラインにも公開できます。"},
   {title:"タイムラインに投稿する",desc:"「自分の旅行」セグメントの右にある「投稿」ボタンから、公開したいタブを選んでタイムラインに投稿できます。編集画面からも公開設定（投稿・更新・停止）を変更できます。"},
   {title:"旅行を共有する",desc:"🔗ボタンから閲覧リンクを発行（ログイン不要）、またはメールアドレスで編集メンバーを招待できます。"},
```

- [ ] **Step 2: 動作確認（preview）**

Run: `preview_eval: window.location.reload()`
1. 「☰ Menu」→「使い方ガイド」を開く。
2. 「メモを残す」の次に「タイムラインに投稿する」項目が表示されることを確認。
3. `preview_console_logs`（level "error"）でエラーが無いことを確認。

- [ ] **Step 3: コミット**

```bash
git add index.html
git commit -m "docs: ガイドにタイムライン投稿の説明を追加"
```

---

## Task 5: 全体フロー検証とデプロイ

- [ ] **Step 1: エンドツーエンド確認（preview）**

Run: `preview_eval: window.location.reload()`。設計仕様（`docs/superpowers/specs/2026-06-12-timeline-publish-design.md`）の検証項目を順に確認し、`preview_console_logs`（level "error"）でエラーが無いこと:

1. オーナーで未公開 → 詳細画面のセグメント右に「投稿」ボタン（globe アイコン）が表示される。クリックで投稿モーダルが開き、タブピッカー＋「投稿する」が表示される。投稿後、同モーダル内が「公開中」表示に切り替わる。
2. オーナーで公開中 → セグメント右に「公開中」ボタン（check アイコン、緑系）。クリックで投稿モーダルが開き、「公開内容を更新する」「公開を停止する」が表示される。
3. 非オーナー／ゲスト／閲覧専用（共有リンク経由）で旅行詳細を開く → 「投稿」「公開中」ボタンは表示されない。
4. 編集モーダル → 一番下にタイムライン公開セクションが表示され、投稿/更新/停止が即時反映される（「保存する」とは独立）。
5. 共有モーダル（🔗ボタン）→ タイムライン公開セクションが無くなり、リンク共有・メンバー招待のみになっている。
6. 画面に絵文字が使われていないこと（「投稿」「公開中」ボタン・投稿モーダルのタイトル・公開中表示はすべて `svgIcon` の globe/check アイコンであること）。

- [ ] **Step 2: 最終スクリーンショット**

Run: `preview_screenshot`（詳細画面・投稿モーダル・編集モーダル下部・共有モーダル 各1枚）。ユーザーへ提示。

- [ ] **Step 3: push してデプロイ**

設計仕様コミット（`e8e73a5`、未push）と本プランの全コミットをまとめて push する。

```bash
git push origin main
```

---

## Self-Review 結果

- **spec カバレッジ**: 設計仕様の 1〜6 すべてに対応するタスクあり（1→Task1, 2→Task1, 3→Task2, 4→Task3, 5→Task1, 6→Task4）。検証6項目はTask5に統合。YAGNI項目（新規アイコン追加・`renderPublishTabPicker`再設計・Firestoreスキーマ変更・`renderFeedCard`変更）は本プランに含めていない。
- **placeholder scan**: 「TBD」「あとで」等の記述なし。すべてのコードブロックは実際に貼り付け可能な完全なコード。
- **型・シグネチャの一致**: `renderPublishSection(withHeading)` は Task1 で定義し、Task1（投稿モーダル, `false`）と Task3（編集モーダル, `true`）で同じシグネチャで呼び出している。`renderListSeg(trailing)` は Task2 で定義し、`renderList()`（変更不要）と `renderDetail()`（`postBtn` または `null`）の両方で整合している。`showPublish` / `publishDraftTabs` の状態リセットは Task1（投稿モーダル open/close）・Task2（ボタンclick）・Task3（編集モーダル open/cancel/save/close）の全エントリ/エグジットポイントで一致している。
