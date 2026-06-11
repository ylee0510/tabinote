# タイムライン機能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 「公開してもいい」と選んだ旅行を専用のタイムライン画面に他ユーザーのカードとして流し、各カードにいいね・コメントを付けられるようにする。投稿者名タップでその人の公開カード一覧も表示する。

**Architecture:** 既存の `trips` に公開フラグ（`publishedToFeed` / `publicTabs`）を足し、公開時にメール等を含まない公開用スナップショットを新規 `feed` コレクションへ複製（`syncFeed`）。タイムライン・閲覧専用詳細・いいね・コメント・公開プロフィールはすべて `feed` だけを読む。タブは単一レジストリ `TAB_DEFS` 駆動にして将来のタブ追加に耐える。

**Tech Stack:** バニラJS（フレームワークなし）、Firebase compat SDK（Auth / Firestore / Storage、CDN読み込み）、単一ファイル `index.html`。ビルド・テストランナーなし。

**検証方針（このリポジトリの実態に合わせた適応）:** 自動テスト基盤が無いため、各タスクは「実装 → preview ツールでブラウザ検証 → コミット」のループで進める。Firebase 呼び出しは本番プロジェクトに飛ぶため、いいね/コメント等の書き込み検証は**検証用の自分のアカウント**で行うこと。preview の起動は `preview_start`、確認は `preview_console_logs` / `preview_snapshot` / `preview_screenshot` を使う。

**全体の前提となる対象ファイル:** すべて `/Users/ylee/Apps/Tavy/index.html` 内の編集（単一ファイルアプリ）。設計の原典は [docs/superpowers/specs/2026-06-11-timeline-feed-design.md](../specs/2026-06-11-timeline-feed-design.md)。

---

## ファイル構成 / 主要シンボル

新規追加するグローバル関数・状態（すべて `index.html` の `<script>` 内）:

- 状態: `listMode`（"mine"|"timeline"）, `profileUserId`, `feedViewId`, `feedItems`(配列), `feedLastDoc`, `feedLoading`, `myLikes`(Set), `publishDraftTabs`(配列)
- 関数: `TAB_DEFS`, `getNickname()`, `setNickname(v)`, `ensureNickname()`, `heartIcon(filled,size)`, `syncFeed(trip)`, `unpublishFeed(tripId)`, `subscribeNothing`(不要), `loadFeed(reset)`, `loadMyLikes()`, `renderFeedCard(item)`, `openFeedTrip(item)`, `toggleLike(item)`, `loadComments(feedId)`, `postComment(feedId,text)`, `deleteComment(feedId,commentId)`, `openUserProfile(uid,name,photo)`, `renderUserProfile()`, `renderFeedDetailExtras(item)`

既存で編集する箇所（行番号は目安、関数名で探すこと）:

- `ICONS`（L690-724）— `heart` / `comment` 追加
- `renderDetail()` のタブバー（L982-988）— `TAB_DEFS` 駆動化＋`publicTabs` フィルタ
- `render()` のビュー分岐（L758-774）— `userProfile` ビューと `listMode` 分岐
- `renderList()`（L904-949）— 上部にアンダーライン切替タブ
- `renderModal_share()`（L1190-1214）— 公開設定セクション追加
- `renderModal_mypage()`（L1558〜）— ニックネーム欄追加
- `upd()`（L550）— 公開中なら `syncFeed` 自動再同期
- `loadProfile()`（L668）後 — プロフィール読込時に何もしないが `getNickname` が参照

---

## Task 1: SVGアイコン（heart / comment）と heartIcon ヘルパー

**Files:**
- Modify: `index.html`（`ICONS` 定義 L690-724、`svgIcon` 定義 L725 直後）

- [ ] **Step 1: ICONS に heart と comment を追加**

`ICONS` オブジェクト末尾の `unlock:'...'`（L723）の後にカンマを足して2行追加する。`unlock` 行末を `,` にし、その下に:

```js
  comment:'<path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8z"/>',
  heart:'<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8z"/>'
```

- [ ] **Step 2: heartIcon ヘルパーを追加**

`svgIcon` 関数定義（L725、`function svgIcon(name,color,size){...}` の行）の直後に新しい関数を追加する。これは塗り（liked）と線（未like）を出し分ける:

```js
function heartIcon(filled,size,color){var s=size||16;var c=color||(filled?"#e0526a":"currentColor");var w=ce("span","",{style:{display:"inline-flex",width:s+"px",height:s+"px",flexShrink:"0"}});w.innerHTML='<svg viewBox="0 0 24 24" width="'+s+'" height="'+s+'" fill="'+(filled?c:"none")+'" stroke="'+c+'" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+ICONS.heart+'</svg>';return w;}
```

- [ ] **Step 3: ブラウザで確認**

`preview_start` でローカルサーバを起動し、`preview_console_logs` でJSエラーが無いこと（構文エラーで全画面が落ちないこと）を確認する。アプリが通常どおり表示されれば合格。

- [ ] **Step 4: コミット**

```bash
git add index.html
git commit -m "feat: タイムライン用にheart/commentアイコンとheartIconヘルパーを追加"
```

---

## Task 2: TAB_DEFS レジストリ化とタブバーの駆動化

**Files:**
- Modify: `index.html`（状態変数付近 L497、`renderDetail()` タブバー L982-988）

- [ ] **Step 1: TAB_DEFS を定義**

`var view="list",selId=null,activeTab="itinerary";`（L497）の直後の行に追加:

```js
var TAB_DEFS=[
  {key:"itinerary",icon:"calendar",label:"行程",always:true},
  {key:"packing",icon:"backpack",label:"持ち物"},
  {key:"todo",icon:"check",label:"ToDo"},
  {key:"places",icon:"pin",label:"スポット"},
  {key:"budget",icon:"money",label:"予算"},
  {key:"weather",icon:"sun",label:"天気"}
];
```

- [ ] **Step 2: タブバーを TAB_DEFS 駆動に置換**

`renderDetail()` 内のタブバー生成（L983 のインライン配列 `[{key:"itinerary",...},...].forEach(...)`）を次に置き換える。`sel._publicTabs` がある場合（feed閲覧時）はそのタブだけ表示する:

```js
  var tabBar=ce("div","tabs");
  var _tabList=sel._publicTabs?TAB_DEFS.filter(function(d){return sel._publicTabs.indexOf(d.key)>=0;}):TAB_DEFS;
  _tabList.forEach(function(x){
    var tb=ce("div","tab"+(activeTab===x.key?" on":""),{onclick:function(){activeTab=x.key;checkInput="";destroyMap();showMap=false;render();}});
    ap(tb,ap(ce("div","tab-ic"),svgIcon(x.icon,"currentColor",20)),ap(ce("div",""),tx(x.label)));
    var cnt=(sel[x.key]&&sel[x.key].length)||0;if(cnt>0)ap(tb,ap(ce("div","tab-n"),tx(String(cnt))));
    ap(tabBar,tb);
  });
```

注: もし feed閲覧時に `activeTab` が公開タブに含まれない場合に備え、置換ブロックの直前で補正する1行を入れる:

```js
  if(sel._publicTabs&&sel._publicTabs.indexOf(activeTab)<0)activeTab=sel._publicTabs[0]||"itinerary";
```

- [ ] **Step 3: ブラウザで確認**

`preview_eval` でリロード後、既存の旅行詳細を開き（`preview_snapshot`）、タブ（行程/持ち物/ToDo/スポット/予算/天気）が従来どおり全て表示・切替できることを確認。`_publicTabs` 未設定なので全タブ出るのが正。

- [ ] **Step 4: コミット**

```bash
git add index.html
git commit -m "refactor: 詳細タブをTAB_DEFSレジストリ駆動に変更"
```

---

## Task 3: ニックネーム（保存・取得・入力プロンプト・プロフィール欄）

**Files:**
- Modify: `index.html`（ヘルパー領域、`renderModal_mypage()` L1558〜、状態変数）

- [ ] **Step 1: ニックネーム getter/setter とプロンプトを追加**

`saveProfile()`（L669）の直後に追加する。`window._tavyProfile` に保存する:

```js
function getNickname(){return (window._tavyProfile&&window._tavyProfile.nickname)?String(window._tavyProfile.nickname).trim():"";}
function setNickname(v){window._tavyProfile=window._tavyProfile||{};window._tavyProfile.nickname=String(v||"").trim().slice(0,20);return saveProfile();}
// 未設定なら入力を促す。設定済み(または入力成功)なら true を返す
async function ensureNickname(){
  if(!user){toast("ログインが必要です");return false;}
  if(getNickname())return true;
  var def=(user.displayName||"").slice(0,20);
  var v=window.prompt("タイムラインで表示するニックネームを入力してください（最大20文字）",def);
  if(v==null)return false;
  v=v.trim();
  if(!v){toast("ニックネームを入力してください");return false;}
  await setNickname(v);
  return true;
}
```

- [ ] **Step 2: プロフィール画面（旅行情報メモ）にニックネーム欄を追加**

`renderModal_mypage()` 内、`var mig=migrateProfile(...)`（L1566）でprofileが確定した直後、最初のセクション（メモ欄）を作る前に挿入する。`m.modal` へ追加するブロック:

```js
  var nickSec=ce("div","",{style:{marginBottom:"22px"}});
  ap(nickSec,ap(ce("div","",{style:{fontSize:"12px",fontWeight:"700",color:"var(--muted)",marginBottom:"8px",letterSpacing:"1px",textTransform:"uppercase"}}),tx("ニックネーム（タイムライン表示名）")));
  var nickIn=ce("input","mypage-val",{placeholder:"例: たびすき",value:profile.nickname||"",maxlength:"20",style:{width:"100%"}});
  nickIn.onblur=function(e){profile.nickname=String(e.target.value||"").trim().slice(0,20);saveProfile();};
  ap(nickSec,nickIn);
  ap(m.modal,nickSec);
```

（`m.modal` への追加位置は、既存のメモセクションを `ap(m.modal, ...)` する行の直前。`renderModal_mypage` 内で `m.modal` ではなく別変数（例 `card`）に追加している場合はそれに合わせること。）

- [ ] **Step 3: ブラウザで確認**

リロード → ☰ Menu → 旅行情報メモ を開き（`preview_click` → `preview_snapshot`）、先頭にニックネーム欄が出ること、入力してフォーカスを外すと保存される（再度開いても値が残る）ことを確認。

- [ ] **Step 4: コミット**

```bash
git add index.html
git commit -m "feat: ニックネーム(公開表示名)の保存とプロフィール欄/入力プロンプトを追加"
```

---

## Task 4: 公開設定UI と syncFeed / 公開停止 / 自動再同期

**Files:**
- Modify: `index.html`（`enableShare` 付近 L620、`upd()` L550、`renderModal_share()` L1190-1214、状態変数）

- [ ] **Step 1: publishDraftTabs 状態を追加**

`var showNewTrip=...,showMyPage=false,guidePage="guide";`（L504）の行の直後に追加:

```js
var publishDraftTabs=null; // 公開設定中に選択中のタブ配列（モーダルを開くとsel.publicTabsで初期化）
```

- [ ] **Step 2: syncFeed と unpublishFeed を追加**

`disableShare`（L621）の直後に追加する。メール・会員IDは含めない:

```js
async function syncFeed(trip){
  if(!user||trip.ownerId!==user.uid)return;
  var tabs=(trip.publicTabs&&trip.publicTabs.length)?trip.publicTabs.slice():["itinerary"];
  if(tabs.indexOf("itinerary")<0)tabs.unshift("itinerary");
  var content={};
  tabs.forEach(function(k){content[k]=trip[k]!==undefined?trip[k]:[];});
  var meta={
    ownerId:trip.ownerId,
    ownerName:getNickname()||"旅人",
    ownerPhoto:(user&&user.photoURL)||null,
    name:trip.name||"",
    destination:trip.destination||"",
    type:trip.type||"overseas",
    coverUrl:trip.coverUrl||null,
    startDate:trip.startDate||"",
    endDate:trip.endDate||"",
    publicTabs:tabs,
    content:content
  };
  var ref=db.collection("feed").doc(trip.id);
  var snap=await ref.get();
  if(snap.exists){
    await ref.set(meta,{merge:true}); // likeCount/commentCount/publishedAtは保持
  }else{
    meta.likeCount=0;meta.commentCount=0;meta.publishedAt=firebase.firestore.FieldValue.serverTimestamp();
    await ref.set(meta);
  }
}
async function unpublishFeed(tripId){
  try{await db.collection("feed").doc(tripId).delete();}catch(e){console.warn("unpublish:",e);}
}
```

- [ ] **Step 3: upd() に公開中の自動再同期を追加**

`upd()`（L550）の本体末尾 `await db.collection("trips").doc(sel.id).update(patch);` の直後に追加:

```js
  if(sel.publishedToFeed){try{var fresh=Object.assign({},sel,patch);await syncFeed(fresh);}catch(e){console.warn("feed resync:",e);}}
```

（`upd` は `getSel()` で `sel` を取得済み。`patch` 適用後の値で再同期する。）

- [ ] **Step 4: 共有モーダルに公開設定セクションを追加**

`renderModal_share()` 内、メンバー招待セクションの前（L1202 の「メンバー招待…」ラベルを作る行の直前）に、オーナー限定で公開設定UIを挿入する:

```js
  if(user&&sel.ownerId===user.uid){
    ap(m.modal,ap(ce("div","",{style:{fontSize:"12px",fontWeight:"700",color:"var(--muted)",margin:"4px 0 8px",textTransform:"uppercase",letterSpacing:"1px"}}),tx("みんなのタイムラインに公開")));
    if(sel.publishedToFeed){
      ap(m.modal,ap(ce("div","",{style:{fontSize:"13px",color:"var(--green)",fontWeight:"700",marginBottom:"8px"}}),tx("✓ タイムラインに公開中")));
      // 公開タブ編集
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

- [ ] **Step 5: タブ選択UIヘルパー renderPublishTabPicker を追加**

`renderModal_share` 関数の**直前**に新しい関数を追加する。行程は常時ON・無効:

```js
function renderPublishTabPicker(){
  var box=ce("div","",{style:{marginBottom:"12px"}});
  TAB_DEFS.forEach(function(d){
    var on=d.always||publishDraftTabs.indexOf(d.key)>=0;
    var row=ce("label","",{style:{display:"flex",alignItems:"center",gap:"10px",padding:"7px 2px",cursor:d.always?"default":"pointer",opacity:d.always?"0.6":"1"}});
    var cb=ce("input","",{type:"checkbox"});cb.checked=on;cb.disabled=!!d.always;
    cb.onchange=function(){if(d.always)return;var i=publishDraftTabs.indexOf(d.key);if(cb.checked&&i<0)publishDraftTabs.push(d.key);else if(!cb.checked&&i>=0)publishDraftTabs.splice(i,1);};
    ap(row,cb,svgIcon(d.icon,"var(--accent)",16),ap(ce("span","",{style:{fontSize:"14px",fontWeight:"600"}}),tx(d.label+(d.always?"（必須）":""))));
    ap(box,row);
  });
  return box;
}
```

- [ ] **Step 6: モーダルを閉じたら下書きをクリア**

`renderModal_share` 末尾の「閉じる」ボタン（L1213）の `onclick:function(){showShare=false;render();}` を `onclick:function(){showShare=false;publishDraftTabs=null;render();}` に変更する。

- [ ] **Step 7: ブラウザで確認（検証用アカウントでログイン）**

リロード → 自分の旅行詳細 → 「共有」→ 公開設定セクションが出る → 行程が必須ON・他タブを選択 → 「タイムラインに公開する」。ニックネーム未設定ならプロンプトが出ることを確認。`preview_console_logs` でエラーが無いこと、Firebaseコンソールで `feed/{tripId}` ドキュメントが作られ、`content` に選択タブのみ・メール非含有・`likeCount=0`・`publishedAt` がある事を確認。続けて「公開を停止する」で `feed` ドキュメントが消える事を確認。

- [ ] **Step 8: コミット**

```bash
git add index.html
git commit -m "feat: 旅行の公開設定UI(公開タブ選択)とsyncFeed/公開停止/自動再同期を追加"
```

---

## Task 5: タイムライン一覧（切替タブ・フィード取得・カード・ページング）

**Files:**
- Modify: `index.html`（状態変数、`renderList()` L904、`render()` 分岐、CSS `<style>` 内）

- [ ] **Step 1: タイムライン用の状態を追加**

L504 付近（`publishDraftTabs` 追加箇所の隣）に追加:

```js
var listMode="mine"; // "mine" | "timeline"
var feedItems=[],feedLastDoc=null,feedLoading=false,feedDone=false;
var myLikes=null; // Set of feedId のlike済み。未ログインはnull
```

- [ ] **Step 2: フィード取得関数とlike状態取得を追加**

`subscribeTrips`（L628）の直後に追加:

```js
async function loadFeed(reset){
  if(feedLoading)return;
  feedLoading=true;
  if(reset){feedItems=[];feedLastDoc=null;feedDone=false;}
  try{
    var q=db.collection("feed").orderBy("publishedAt","desc").limit(30);
    if(feedLastDoc)q=q.startAfter(feedLastDoc);
    var snap=await q.get();
    snap.docs.forEach(function(d){feedItems.push(Object.assign({id:d.id},d.data()));});
    feedLastDoc=snap.docs.length?snap.docs[snap.docs.length-1]:feedLastDoc;
    if(snap.docs.length<30)feedDone=true;
  }catch(e){console.warn("loadFeed:",e);toast("タイムラインの取得に失敗しました");}
  feedLoading=false;
  render();
}
async function loadMyLikes(){
  if(!user){myLikes=null;return;}
  myLikes=new Set();
  try{
    var snap=await db.collectionGroup("likes").where("uid","==",user.uid).get();
    snap.docs.forEach(function(d){var p=d.ref.parent.parent;if(p)myLikes.add(p.id);});
  }catch(e){console.warn("loadMyLikes:",e);}
  render();
}
```

- [ ] **Step 3: 切替時にフィードを読み込む関数を追加**

Step 2 の直後に追加:

```js
function switchListMode(mode){
  listMode=mode;
  if(mode==="timeline"){
    if(feedItems.length===0)loadFeed(true);
    if(user&&myLikes===null)loadMyLikes();
  }
  render();
}
```

- [ ] **Step 4: renderList の先頭にアンダーライン切替タブを追加し、timeline時はフィードを描画**

`function renderList(){`（L904）直後に切替タブを差し込み、`listMode==="timeline"` のときはフィードカード一覧を返す。関数の頭を次の構成にする（既存の「自分の旅行」描画は `else` 側に残す）:

```js
function renderList(){
  var outer=ce("div","");
  // 切替タブ（自分の旅行 / タイムライン）
  var seg=ce("div","feed-seg");
  var t1=ce("div","feed-seg-tab"+(listMode==="mine"?" on":""),{onclick:function(){switchListMode("mine");}});ap(t1,tx("自分の旅行"));
  var t2=ce("div","feed-seg-tab"+(listMode==="timeline"?" on":""),{onclick:function(){switchListMode("timeline");}});ap(t2,tx("タイムライン"));
  ap(seg,t1,t2);ap(outer,seg);

  if(listMode==="timeline"){
    if(feedLoading&&feedItems.length===0){ap(outer,ap(ce("div","",{style:{textAlign:"center",padding:"60px 0",color:"var(--muted)"}}),tx("読み込み中…")));return outer;}
    if(feedItems.length===0){ap(outer,ap(ce("div","",{style:{textAlign:"center",padding:"60px 24px",color:"var(--muted)"}}),tx("まだ公開された旅行がありません")));return outer;}
    var feedWrap=ce("div","feed-list");
    feedItems.forEach(function(item){ap(feedWrap,renderFeedCard(item));});
    ap(outer,feedWrap);
    if(!feedDone){ap(outer,ap(ce("button","feed-more-btn",{onclick:function(){loadFeed(false);}}),tx(feedLoading?"読み込み中…":"もっと見る")));}
    return outer;
  }

  // 以下は従来の「自分の旅行」一覧（既存コードをこの位置に移動）
```

そして既存の `renderList` 本体（`if(trips.length===0){...}` 以降〜 `return d;`）を、上記の続きとして残す。ただし最後の `return d;` の前に従来の `d`（trip-list）を `outer` に足して `outer` を返すよう変更する: 既存の `return d;`（L948）を次に置換:

```js
  ap(outer,d);
  return outer;
}
```

また `trips.length===0` の早期 return（L908 `return d;`）も `ap(outer,d);return outer;` に置換する。

- [ ] **Step 5: renderFeedCard を追加**

`renderList` の直後に追加。カバー110px・タイプバッジ・投稿者・タイトル・メタ・公開タブchip・いいね/コメント。投稿者名タップで `openUserProfile`、カード本体タップで `openFeedTrip`:

```js
function relTime(ts){if(!ts||!ts.seconds)return "";var diff=Date.now()/1000-ts.seconds;if(diff<3600)return Math.max(1,Math.floor(diff/60))+"分前";if(diff<86400)return Math.floor(diff/3600)+"時間前";if(diff<2592000)return Math.floor(diff/86400)+"日前";return Math.floor(diff/2592000)+"ヶ月前";}
function renderFeedCard(item){
  var card=ce("div","feed-card");
  // カバー
  var cov=ce("div","feed-card-cover",{onclick:function(){openFeedTrip(item);}});
  if(item.coverUrl){var img=document.createElement("img");img.className="feed-card-cover-img";img.src=item.coverUrl;ap(cov,img);}
  else{cov.style.background=getTripColor(item.id);}
  ap(cov,ap(ce("span","feed-card-type"),tx(item.type==="overseas"?"🌏 海外":"🏠 国内")));
  ap(card,cov);
  // ボディ
  var body=ce("div","feed-card-body",{onclick:function(){openFeedTrip(item);}});
  var owner=ce("div","feed-card-owner");
  var ava=ce("div","feed-card-ava",{onclick:function(e){e.stopPropagation();openUserProfile(item.ownerId,item.ownerName,item.ownerPhoto);}});
  if(item.ownerPhoto){var pi=document.createElement("img");pi.src=item.ownerPhoto;pi.style.cssText="width:100%;height:100%;border-radius:50%;object-fit:cover";ap(ava,pi);}else{ap(ava,tx((item.ownerName||"?")[0].toUpperCase()));}
  var oname=ce("span","feed-card-oname",{onclick:function(e){e.stopPropagation();openUserProfile(item.ownerId,item.ownerName,item.ownerPhoto);}});ap(oname,tx((item.ownerName||"旅人")+" · "+relTime(item.publishedAt)));
  ap(owner,ava,oname);ap(body,owner);
  ap(body,ap(ce("div","feed-card-title"),tx(item.name||"無題の旅行")));
  var meta=ce("div","feed-card-meta");
  if(item.destination)ap(meta,ap(ce("span",""),tx("📍 "+item.destination)));
  if(item.startDate)ap(meta,ap(ce("span",""),tx(item.startDate+(item.endDate?" → "+item.endDate:""))));
  ap(body,meta);
  var chips=ce("div","feed-card-chips");
  (item.publicTabs||[]).forEach(function(k){var d=TAB_DEFS.find(function(t){return t.key===k;});if(d)ap(chips,ap(ce("span","feed-card-chip"),tx(d.label)));});
  ap(body,chips);
  ap(card,body);
  // アクション
  var acts=ce("div","feed-card-acts");
  var liked=!!(myLikes&&myLikes.has(item.id));
  var likeBtn=ce("div","feed-card-act"+(liked?" liked":""),{onclick:function(e){e.stopPropagation();toggleLike(item);}});
  ap(likeBtn,heartIcon(liked,16),ap(ce("span",""),tx(String(item.likeCount||0))));
  var cmtBtn=ce("div","feed-card-act",{onclick:function(e){e.stopPropagation();openFeedTrip(item);}});
  ap(cmtBtn,svgIcon("comment","currentColor",16),ap(ce("span",""),tx(String(item.commentCount||0))));
  ap(acts,likeBtn,cmtBtn);ap(card,acts);
  return card;
}
```

- [ ] **Step 6: CSS を追加**

`<style>` 内（例: `.trip-card{...}` L75 付近）に追記:

```css
.feed-seg{display:flex;gap:22px;padding:6px 16px 0;border-bottom:1px solid var(--border);margin-bottom:14px;}
.feed-seg-tab{font-size:15px;font-weight:800;padding:8px 2px 11px;color:var(--muted);position:relative;cursor:pointer;}
.feed-seg-tab.on{color:var(--ink);}
.feed-seg-tab.on::after{content:'';position:absolute;left:0;right:0;bottom:-1px;height:2.5px;background:var(--accent);border-radius:2px;}
.feed-list{display:flex;flex-direction:column;gap:14px;}
.feed-card{background:var(--paper);border:1px solid var(--border);border-radius:16px;overflow:hidden;cursor:pointer;}
.feed-card-cover{position:relative;width:100%;height:110px;}
.feed-card-cover-img{width:100%;height:110px;object-fit:cover;display:block;}
.feed-card-type{position:absolute;top:10px;left:10px;background:rgba(0,0,0,.55);color:#fff;font-size:11px;font-weight:700;padding:3px 9px;border-radius:20px;}
.feed-card-body{padding:11px 14px 4px;}
.feed-card-owner{display:flex;align-items:center;gap:7px;margin-bottom:7px;}
.feed-card-ava{width:26px;height:26px;border-radius:50%;background:var(--accent);color:#fff;font-size:12px;font-weight:800;display:flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0;overflow:hidden;}
.feed-card-oname{font-size:12px;color:var(--muted);font-weight:600;cursor:pointer;}
.feed-card-title{font-size:16px;font-weight:800;color:var(--ink);margin-bottom:3px;}
.feed-card-meta{display:flex;gap:8px;flex-wrap:wrap;font-size:12px;color:var(--muted);}
.feed-card-chips{display:flex;gap:5px;flex-wrap:wrap;margin:9px 0 2px;}
.feed-card-chip{background:var(--stamp);color:var(--muted);font-size:10px;font-weight:700;padding:2px 8px;border-radius:7px;}
.feed-card-acts{display:flex;gap:18px;padding:9px 14px 12px;border-top:1px solid var(--border);margin-top:8px;}
.feed-card-act{display:flex;align-items:center;gap:5px;font-size:13px;color:var(--muted);font-weight:700;cursor:pointer;}
.feed-card-act.liked{color:#e0526a;}
.feed-more-btn{display:block;width:100%;margin:14px 0 0;padding:12px;background:none;border:1px solid var(--border);border-radius:12px;font-size:13px;font-weight:700;color:var(--muted);cursor:pointer;font-family:inherit;}
```

- [ ] **Step 7: ブラウザで確認**

リロード → 一覧上部に「自分の旅行 / タイムライン」タブ。タイムラインを押すと Task4 で公開したカードが出る（`preview_snapshot` / `preview_screenshot`）。カバー110px・タイプバッジ・公開タブchip・いいね/コメント数が表示されること、`preview_console_logs` でエラーが無いことを確認。

- [ ] **Step 8: コミット**

```bash
git add index.html
git commit -m "feat: タイムライン切替タブとフィード取得・カード・ページングを追加"
```

---

## Task 6: フィードカードのタップで閲覧専用詳細を開く

**Files:**
- Modify: `index.html`（`openFeedTrip` 追加、`render()` の戻る/ヘッダー周辺、状態変数）

- [ ] **Step 1: feedViewId 状態を追加**

L504 付近に追加:

```js
var feedViewId=null; // 現在閲覧中のfeedアイテムID（feed由来の閲覧専用詳細）
```

- [ ] **Step 2: openFeedTrip を追加**

`loadSharedTrip`（L622）の直後に追加。`content` を top-level に展開し、`_publicTabs` を付け、既存の閲覧専用モードに載せる:

```js
function openFeedTrip(item){
  var vo=Object.assign({id:item.id,name:item.name,destination:item.destination,type:item.type,coverUrl:item.coverUrl,startDate:item.startDate,endDate:item.endDate},item.content||{});
  vo._publicTabs=(item.publicTabs||["itinerary"]).slice();
  viewOnlyTrip=vo;isViewOnly=true;feedViewId=item.id;selId=item.id;
  view="detail";activeTab=vo._publicTabs[0]||"itinerary";
  track('feed_open',{});
  render();
}
```

- [ ] **Step 3: 閲覧専用の戻る処理で feedViewId をクリア**

`render()` 内の戻るボタン（L842）`onclick:function(){if(isViewOnly){isViewOnly=false;viewOnlyTrip=null;selId=null;window.history.pushState(...);}...}` を、feed由来の場合は一覧（タイムライン）へ戻すよう修正する。該当 onclick を次に置換:

```js
    var bb=ce("button","back-btn",{onclick:function(){var wasFeed=!!feedViewId;if(isViewOnly){isViewOnly=false;viewOnlyTrip=null;selId=null;feedViewId=null;if(!wasFeed)window.history.pushState({},"","https://gotavy.com/");}destroyMap();showMap=false;view="list";if(wasFeed)listMode="timeline";render();}});
```

- [ ] **Step 4: ブラウザで確認**

タイムラインのカードをタップ → 閲覧専用詳細が開く（`preview_snapshot`）。公開タブだけがタブバーに出ること、行程など中身が表示されること、戻るとタイムラインに戻ることを確認。非公開タブ（例: 予算を公開していない旅行）が出ないことを確認。

- [ ] **Step 5: コミット**

```bash
git add index.html
git commit -m "feat: フィードカードのタップでスナップショットから閲覧専用詳細を開く"
```

---

## Task 7: いいね（トグル・カウンタ・トランザクション）

**Files:**
- Modify: `index.html`（`toggleLike` 追加、詳細画面下部に like 表示）

- [ ] **Step 1: toggleLike を追加**

`openFeedTrip`（Task6）の直後に追加。トランザクションで `likeCount` 増減、`likes/{uid}` を set/delete、`myLikes` をローカル更新:

```js
async function toggleLike(item){
  if(!user){toast("ログインするといいねできます");return;}
  var liked=!!(myLikes&&myLikes.has(item.id));
  var feedRef=db.collection("feed").doc(item.id);
  var likeRef=feedRef.collection("likes").doc(user.uid);
  // 楽観的更新
  myLikes=myLikes||new Set();
  if(liked){myLikes.delete(item.id);item.likeCount=Math.max(0,(item.likeCount||0)-1);}
  else{myLikes.add(item.id);item.likeCount=(item.likeCount||0)+1;}
  render();
  try{
    await db.runTransaction(async function(tx){
      var f=await tx.get(feedRef);if(!f.exists)return;
      var c=f.data().likeCount||0;
      if(liked){tx.delete(likeRef);tx.update(feedRef,{likeCount:Math.max(0,c-1)});}
      else{tx.set(likeRef,{uid:user.uid,createdAt:firebase.firestore.FieldValue.serverTimestamp()});tx.update(feedRef,{likeCount:c+1});}
    });
  }catch(e){console.warn("toggleLike:",e);toast("いいねに失敗しました");
    // ロールバック
    if(liked){myLikes.add(item.id);item.likeCount=(item.likeCount||0)+1;}else{myLikes.delete(item.id);item.likeCount=Math.max(0,(item.likeCount||0)-1);}
    render();
  }
}
```

- [ ] **Step 2: 閲覧専用詳細（feed由来）にいいね＋コメント欄を出すフックを追加**

`renderDetail()` の末尾、`return wrap;` の直前に、feed閲覧時のみ追加ブロックを差し込む:

```js
  if(feedViewId){
    var _fi=feedItems.find(function(x){return x.id===feedViewId;})||{id:feedViewId,likeCount:0,commentCount:0};
    ap(wrap,renderFeedDetailExtras(_fi));
  }
```

（`renderDetail` が `return wrap;` でないローカル変数名の場合はそれに合わせる。L963 で `var wrap=ce("div","");`、最終的に `wrap` を返している。）

- [ ] **Step 3: renderFeedDetailExtras（いいね行のみ。コメントはTask8で追記）を追加**

`renderFeedCard` の直後に追加。まずはいいねバーだけ実装し、Task8 でコメントを足す:

```js
function renderFeedDetailExtras(item){
  var box=ce("div","feed-detail-extras");
  var liked=!!(myLikes&&myLikes.has(item.id));
  var bar=ce("div","feed-detail-likebar");
  var likeBtn=ce("div","feed-card-act"+(liked?" liked":""),{onclick:function(){toggleLike(item);}});
  ap(likeBtn,heartIcon(liked,20),ap(ce("span",""),tx(String(item.likeCount||0)+" いいね")));
  ap(bar,likeBtn);ap(box,bar);
  return box;
}
```

- [ ] **Step 4: CSS を追加**

`<style>` 内に追記:

```css
.feed-detail-extras{padding:14px 16px 40px;}
.feed-detail-likebar{display:flex;gap:18px;padding:12px 0;border-bottom:1px solid var(--border);}
```

- [ ] **Step 5: ブラウザで確認（検証用アカウント）**

タイムラインのカードでハートを押す → 塗り＋カウント増。再押下で戻る。詳細画面下部のいいねバーでも同様に動くこと。リロード後もlike状態（塗り）が復元されること（`loadMyLikes`）。Firebaseコンソールで `feed/{id}/likes/{uid}` と `likeCount` を確認。

- [ ] **Step 6: コミット**

```bash
git add index.html
git commit -m "feat: フィードのいいね(トグル/カウンタ/like状態復元)を追加"
```

---

## Task 8: コメント（一覧・投稿・削除・カウンタ）

**Files:**
- Modify: `index.html`（コメント関数群、`renderFeedDetailExtras` にコメントUI追記、状態変数）

- [ ] **Step 1: コメント用状態を追加**

L504 付近に追加:

```js
var feedComments=[],feedCommentsFor=null,commentInput="";
```

- [ ] **Step 2: コメント取得・投稿・削除を追加**

`toggleLike`（Task7）の直後に追加:

```js
async function loadComments(feedId){
  feedCommentsFor=feedId;feedComments=[];
  try{
    var snap=await db.collection("feed").doc(feedId).collection("comments").orderBy("createdAt","asc").get();
    feedComments=snap.docs.map(function(d){return Object.assign({id:d.id},d.data());});
  }catch(e){console.warn("loadComments:",e);}
  render();
}
async function postComment(feedId){
  if(!user){toast("ログインするとコメントできます");return;}
  var text=(commentInput||"").trim();
  if(!text)return;
  if(text.length>500){toast("コメントは500文字以内です");return;}
  if(!(await ensureNickname())){render();return;}
  var feedRef=db.collection("feed").doc(feedId);
  try{
    await feedRef.collection("comments").add({uid:user.uid,name:getNickname()||"旅人",text:text,createdAt:firebase.firestore.FieldValue.serverTimestamp()});
    await feedRef.update({commentCount:firebase.firestore.FieldValue.increment(1)});
    commentInput="";
    var _fi=feedItems.find(function(x){return x.id===feedId;});if(_fi)_fi.commentCount=(_fi.commentCount||0)+1;
    await loadComments(feedId);
    track('feed_comment',{});
  }catch(e){console.warn("postComment:",e);toast("コメントに失敗しました");}
}
async function deleteComment(feedId,commentId){
  if(!confirm("このコメントを削除しますか？"))return;
  var feedRef=db.collection("feed").doc(feedId);
  try{
    await feedRef.collection("comments").doc(commentId).delete();
    await feedRef.update({commentCount:firebase.firestore.FieldValue.increment(-1)});
    var _fi=feedItems.find(function(x){return x.id===feedId;});if(_fi)_fi.commentCount=Math.max(0,(_fi.commentCount||0)-1);
    await loadComments(feedId);
  }catch(e){console.warn("deleteComment:",e);toast("削除に失敗しました");}
}
```

- [ ] **Step 3: 詳細を開いたときにコメントを読み込む**

`openFeedTrip`（Task6）の `render();` の直前に追加:

```js
  loadComments(item.id);
```

- [ ] **Step 4: renderFeedDetailExtras にコメントUIを追記**

Task7 の `renderFeedDetailExtras` の `ap(box,bar);` の後、`return box;` の前に追加:

```js
  // コメント一覧
  var cwrap=ce("div","feed-comments");
  ap(cwrap,ap(ce("div","feed-comments-h"),tx("コメント "+(item.commentCount||0))));
  var list=(feedCommentsFor===item.id)?feedComments:[];
  if(list.length===0){ap(cwrap,ap(ce("div","",{style:{fontSize:"13px",color:"var(--muted)",padding:"8px 0"}}),tx("まだコメントはありません")));}
  list.forEach(function(c){
    var row=ce("div","feed-comment");
    var ava=ce("div","feed-comment-ava",{onclick:function(){openUserProfile(c.uid,c.name,null);}});ap(ava,tx((c.name||"?")[0].toUpperCase()));
    var main=ce("div","feed-comment-main");
    var top=ce("div","feed-comment-top");
    var nm=ce("span","feed-comment-name",{onclick:function(){openUserProfile(c.uid,c.name,null);}});ap(nm,tx(c.name||"旅人"));
    ap(top,nm,ap(ce("span","feed-comment-time"),tx(relTime(c.createdAt))));
    ap(main,top,ap(ce("div","feed-comment-text"),tx(c.text||"")));
    if(user&&c.uid===user.uid){var del=ce("button","feed-comment-del",{onclick:function(){deleteComment(item.id,c.id);}});ap(del,tx("削除"));ap(main,del);}
    ap(row,ava,main);ap(cwrap,row);
  });
  // 入力欄
  if(user){
    var inRow=ce("div","feed-comment-inrow");
    var inp=ce("input","finp",{placeholder:"コメントを書く…",value:commentInput,maxlength:"500",oninput:function(e){commentInput=e.target.value;},onkeydown:function(e){if(e.key==="Enter"){postComment(item.id);}}});
    var sb=ce("button","plus-btn",{onclick:function(){postComment(item.id);}});ap(sb,tx("送信"));
    ap(inRow,inp,sb);ap(cwrap,inRow);
  }else{
    ap(cwrap,ap(ce("div","",{style:{fontSize:"13px",color:"var(--muted)",padding:"10px 0"}}),tx("ログインするとコメントできます")));
  }
  ap(box,cwrap);
```

- [ ] **Step 5: CSS を追加**

`<style>` 内に追記:

```css
.feed-comments{margin-top:16px;}
.feed-comments-h{font-size:13px;font-weight:800;color:var(--ink);margin-bottom:10px;}
.feed-comment{display:flex;gap:9px;padding:9px 0;border-bottom:1px solid var(--border);}
.feed-comment-ava{width:28px;height:28px;border-radius:50%;background:var(--accent);color:#fff;font-size:12px;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0;cursor:pointer;}
.feed-comment-main{flex:1;min-width:0;}
.feed-comment-top{display:flex;align-items:center;gap:8px;margin-bottom:2px;}
.feed-comment-name{font-size:13px;font-weight:700;color:var(--ink);cursor:pointer;}
.feed-comment-time{font-size:11px;color:var(--muted);}
.feed-comment-text{font-size:14px;color:var(--ink);line-height:1.5;word-break:break-word;}
.feed-comment-del{background:none;border:none;color:#ccc;font-size:11px;cursor:pointer;font-family:inherit;margin-top:3px;padding:0;}
.feed-comment-inrow{display:flex;gap:8px;margin-top:12px;}
```

- [ ] **Step 6: ブラウザで確認（検証用アカウント）**

カードタップ → 詳細下部にコメント欄。コメント投稿 → 一覧に出てカウント増（カードのコメント数も増える）。ニックネーム未設定ならプロンプト。自分のコメントに削除ボタン → 削除でカウント減。未ログイン時は「ログインするとコメントできます」。`preview_console_logs` でエラー無し、Firebaseで `comments` サブコレクションと `commentCount` を確認。

- [ ] **Step 7: コミット**

```bash
git add index.html
git commit -m "feat: フィードのコメント(一覧/投稿/削除/カウンタ)を追加"
```

---

## Task 9: ユーザー公開プロフィール画面

**Files:**
- Modify: `index.html`（`openUserProfile` / `renderUserProfile` 追加、`render()` 分岐、状態変数、ヘッダー戻る）

- [ ] **Step 1: プロフィール用状態を追加**

L504 付近に追加:

```js
var profileUserId=null,profileUserName="",profileUserPhoto=null,profileFeed=[],profileLoading=false;
```

- [ ] **Step 2: openUserProfile と取得を追加**

`renderFeedCard` 付近（同じ関数群の近く）に追加:

```js
async function openUserProfile(uid,name,photo){
  if(!uid)return;
  profileUserId=uid;profileUserName=name||"";profileUserPhoto=photo||null;profileFeed=[];profileLoading=true;
  // 閲覧専用詳細から来た場合は閉じる
  if(isViewOnly){isViewOnly=false;viewOnlyTrip=null;feedViewId=null;}
  view="userProfile";
  render();
  try{
    var snap=await db.collection("feed").where("ownerId","==",uid).orderBy("publishedAt","desc").limit(50).get();
    profileFeed=snap.docs.map(function(d){return Object.assign({id:d.id},d.data());});
    if(profileFeed.length&&profileFeed[0].ownerName)profileUserName=profileFeed[0].ownerName;
    if(profileFeed.length&&profileFeed[0].ownerPhoto)profileUserPhoto=profileFeed[0].ownerPhoto;
  }catch(e){console.warn("openUserProfile:",e);toast("プロフィールの取得に失敗しました");}
  profileLoading=false;
  render();
}
```

- [ ] **Step 3: renderUserProfile を追加**

`openUserProfile` の直後に追加。ヘッダー＋カード一覧（`renderFeedCard` 再利用）:

```js
function renderUserProfile(){
  var wrap=ce("div","");
  var head=ce("div","profile-head");
  var ava=ce("div","profile-ava");
  if(profileUserPhoto){var pi=document.createElement("img");pi.src=profileUserPhoto;pi.style.cssText="width:100%;height:100%;border-radius:50%;object-fit:cover";ap(ava,pi);}else{ap(ava,tx((profileUserName||"?")[0].toUpperCase()));}
  ap(head,ava);
  ap(head,ap(ce("div","profile-name"),tx(profileUserName||"旅人")));
  ap(head,ap(ce("div","profile-count"),tx(profileLoading?"読み込み中…":("公開した旅行 "+profileFeed.length+"件"))));
  ap(wrap,head);
  if(!profileLoading&&profileFeed.length===0){ap(wrap,ap(ce("div","",{style:{textAlign:"center",padding:"50px 24px",color:"var(--muted)"}}),tx("公開された旅行がありません")));return wrap;}
  var list=ce("div","feed-list");
  profileFeed.forEach(function(item){ap(list,renderFeedCard(item));});
  ap(wrap,list);
  return wrap;
}
```

- [ ] **Step 4: render() に userProfile ビューを追加**

`render()` のビュー分岐、ワイド版（L762-764）と狭幅版（L768-773）の両方に `userProfile` を足す。ワイド側 `main` 構築（L762付近）に追加:

```js
    if(view==="userProfile")ap(main,renderUserProfile());
    else if(view==="detail")ap(main,renderDetail());
    else if(view==="templates")ap(main,renderTemplates());
    else ap(main,renderList());
```

狭幅側（L768付近）の分岐に追加（`view==="list"` の前後どこでもよいが分岐として）:

```js
    if(view==="userProfile")ap(wrap,renderUserProfile());
    else if(view==="list"){ap(wrap,renderList()); /* 既存の利用規約フッターはそのまま */
```

（既存の `if(view==="list"){...}` を `else if(view==="list"){...}` に変更し、その前に `if(view==="userProfile")ap(wrap,renderUserProfile());` を置く。）

- [ ] **Step 5: ヘッダーに userProfile の戻るボタンを出す**

`render()` のヘッダー条件 `if(isViewOnly||(!isWide&&(view==="detail"||view==="templates")))`（L841）に `view==="userProfile"` を加える:

```js
  if(isViewOnly||view==="userProfile"||(!isWide&&(view==="detail"||view==="templates"))){
```

そして戻るボタンの `onclick`（Task6 で修正済みのもの）を、`userProfile` の場合はタイムラインへ戻すよう調整する。Task6 の onclick を次に再置換:

```js
    var bb=ce("button","back-btn",{onclick:function(){if(view==="userProfile"){view="list";listMode="timeline";profileUserId=null;render();return;}var wasFeed=!!feedViewId;if(isViewOnly){isViewOnly=false;viewOnlyTrip=null;selId=null;feedViewId=null;if(!wasFeed)window.history.pushState({},"","https://gotavy.com/");}destroyMap();showMap=false;view="list";if(wasFeed)listMode="timeline";render();}});
```

ヘッダータイトル（L852）も userProfile 時に名前を出すよう、`tx(...)` の三項に分岐を足す:

```js
    ap(ht,tx(isViewOnly?(sel?sel.name:"閲覧"):view==="userProfile"?(profileUserName||"プロフィール"):view==="list"?"Tavy":view==="templates"?"マイ持ち物リスト":(sel?sel.name:"")));
```

- [ ] **Step 6: CSS を追加**

`<style>` 内に追記:

```css
.profile-head{display:flex;flex-direction:column;align-items:center;text-align:center;padding:24px 16px 18px;}
.profile-ava{width:64px;height:64px;border-radius:50%;background:var(--accent);color:#fff;font-size:26px;font-weight:800;display:flex;align-items:center;justify-content:center;margin-bottom:10px;overflow:hidden;}
.profile-name{font-size:18px;font-weight:800;color:var(--ink);margin-bottom:3px;}
.profile-count{font-size:13px;color:var(--muted);margin-bottom:6px;}
```

- [ ] **Step 7: ブラウザで確認**

タイムラインのカードで投稿者名（またはアバター）をタップ → プロフィール画面。ヘッダーに名前＋公開件数、その人のカード一覧が出る。カードをタップで閲覧専用詳細へ。コメント欄の投稿者名タップでもプロフィールに飛ぶこと。戻るとタイムラインへ。`preview_console_logs` でエラー無しを確認。

- [ ] **Step 8: コミット**

```bash
git add index.html
git commit -m "feat: ユーザー公開プロフィール画面と投稿者名タップ導線を追加"
```

---

## Task 10: Firestore セキュリティルール / インデックス（Firebaseコンソール作業）

**Files:**
- 影響: Firebase コンソール（コードのデプロイとは別。`firestore.rules` をリポジトリ管理していないため手動更新。リポジトリに記録として `docs/firestore-feed-rules.md` を残す）

- [ ] **Step 1: ルール文書をリポジトリに残す**

`docs/firestore-feed-rules.md` を新規作成し、適用すべきルールを記録する:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // ... 既存の trips / users ルールはそのまま ...

    match /feed/{tripId} {
      allow read: if true;
      allow create, delete: if request.auth != null
        && request.auth.uid == request.resource.data.ownerId;
      // 本人=全更新可。他人=likeCount/commentCountの変更のみ許可
      allow update: if request.auth != null && (
        request.auth.uid == resource.data.ownerId ||
        request.resource.data.diff(resource.data).affectedKeys()
          .hasOnly(['likeCount','commentCount'])
      );

      match /likes/{uid} {
        allow read: if true;
        allow create, delete: if request.auth != null && request.auth.uid == uid
          && uid == request.resource.data.uid;
      }
      match /comments/{cid} {
        allow read: if true;
        allow create: if request.auth != null
          && request.auth.uid == request.resource.data.uid
          && request.resource.data.text is string
          && request.resource.data.text.size() > 0
          && request.resource.data.text.size() <= 500;
        allow delete: if request.auth != null
          && request.auth.uid == resource.data.uid;
      }
    }
  }
}
```

注: `likes` の `delete` 時は `request.resource.data` が無いので、削除許可は `request.auth.uid == uid` のみで判定される（上の `create, delete` 結合ルールで delete 時は後半条件が無視される点に注意。厳密に分けるなら delete を別行 `allow delete: if request.auth != null && request.auth.uid == uid;` にする）。実運用では create と delete を分けて書くこと:

```
        allow create: if request.auth != null && request.auth.uid == uid
          && uid == request.resource.data.uid;
        allow delete: if request.auth != null && request.auth.uid == uid;
```

- [ ] **Step 2: コンソールでルールを適用**

Firebase コンソール → Firestore Database → ルール に上記を反映して「公開」。

- [ ] **Step 3: 複合インデックスを作成**

以下2つのインデックスを作成（コンソールが要求するリンクからでも可）:
- コレクション `feed`: `ownerId`（昇順）＋ `publishedAt`（降順）— 公開プロフィール用
- コレクショングループ `likes`: `uid`（昇順）— `loadMyLikes` の collectionGroup クエリ用

タイムライン本体（`feed` の `publishedAt` 単独降順）は単一フィールドインデックスで自動対応。

- [ ] **Step 4: 動作確認**

- 別アカウント（または未ログイン）でタイムラインが読めること
- 他人の `feed` ドキュメントを直接編集できない（オーナー以外は likeCount/commentCount 以外不可）こと
- いいね・コメントが正しく書け、他人のコメントは削除できないこと
- 公開プロフィールのクエリがインデックスエラーにならないこと（`preview_console_logs` で `FAILED_PRECONDITION` が出ないこと）

- [ ] **Step 5: コミット**

```bash
git add docs/firestore-feed-rules.md
git commit -m "docs: feedコレクションのセキュリティルール/インデックスを記録"
```

---

## Self-Review チェック結果

- **Spec coverage:** 同意フラグ(T4)/権限(T4,7,8,10)/feedスナップショット(T4)/公開タブ選択(T2,4)/カードデザイン(T5)/アンダーライン切替(T5)/SVGアイコン(T1)/ニックネーム(T3)＋反映(T4,8)/閲覧専用詳細(T6)/いいね(T7)/コメント(T8)/公開プロフィール(T9)/タブ拡張性=レジストリ(T2)/セキュリティルール・インデックス(T10) — 全項目に対応タスクあり。
- **Placeholder scan:** 各コード手順は実コードを記載。TBD等なし。
- **Type consistency:** `syncFeed(trip)`/`unpublishFeed(id)`/`loadFeed(reset)`/`renderFeedCard(item)`/`openFeedTrip(item)`/`toggleLike(item)`/`loadComments(id)`/`postComment(id)`/`deleteComment(id,cid)`/`openUserProfile(uid,name,photo)`/`renderUserProfile()`/`renderFeedDetailExtras(item)`/`getNickname()`/`ensureNickname()`/`heartIcon(filled,size,color)` をタスク間で同名・同シグネチャで使用。`feedViewId` / `myLikes` / `listMode` / `publishDraftTabs` の参照も一貫。

## スコープ外（実装しない）

通報・ブロック・モデレーション、ハッシュタグ/検索/フォロー、コメント返信スレッド・コメントへのいいね、無限スクロール（「もっと見る」採用）、通知。
