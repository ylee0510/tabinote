# Cover Photo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 旅行カードと詳細ヘッダーにカバー写真（なければ決定論的単色）を表示し、カードと詳細の両方からアップロードできるようにする。

**Architecture:** `index.html` 単一ファイルに `getTripColor()` / `resizeCoverImage()` / `uploadCoverPhoto()` を追加し、`renderList()` と `renderDetail()` の hero エリアを変更する。写真は Firebase Storage に `users/{uid}/covers/{tripId}.jpg` で保存、URL を Firestore の `coverUrl` フィールドに保存する。

**Tech Stack:** Vanilla HTML/CSS/JS、Firebase Storage / Firestore（既存）

---

### Task 1: CSS — カバー写真スタイル追加

**Files:**
- Modify: `index.html` — `<style>` ブロック（`.guest-banner` の直後付近、line 178付近）

- [ ] **Step 1: カバー関連CSSを追加する**

`.guest-try-btn{...}` の直後（`</style>` の前）に以下を追加する:

```css
.trip-card.has-cover{padding-top:0;}
.trip-card.has-cover::before{display:none;}
.trip-card-cover-wrap{position:relative;width:100%;height:110px;border-radius:14px 14px 0 0;overflow:hidden;cursor:default;}
.trip-card-cover-img{width:100%;height:110px;object-fit:cover;display:block;}
.trip-card-cover-btn{position:absolute;bottom:7px;right:8px;background:rgba(0,0,0,0.45);border:none;color:#fff;border-radius:8px;padding:4px 8px;font-size:12px;cursor:pointer;backdrop-filter:blur(2px);}
.hero-cover-wrap{position:relative;width:100%;height:140px;overflow:hidden;}
.hero-cover-img{width:100%;height:140px;object-fit:cover;display:block;}
.hero-cover-placeholder{width:100%;height:140px;}
.hero-cover-btn{position:absolute;bottom:8px;right:12px;background:rgba(0,0,0,0.45);border:none;color:#fff;border-radius:8px;padding:5px 10px;font-size:12px;cursor:pointer;backdrop-filter:blur(2px);}
```

- [ ] **Step 2: コミットする**

```bash
git add index.html
git commit -m "feat: add cover photo CSS styles"
```

---

### Task 2: JS — ヘルパー関数3つを追加

**Files:**
- Modify: `index.html` — `uploadAttachment()` 関数（line 473付近）の直後に追加

- [ ] **Step 1: `getTripColor()` / `resizeCoverImage()` / `uploadCoverPhoto()` を追加する**

`async function uploadAttachment(...){}` の直後に以下を挿入する:

```js
var COVER_COLORS=["#2d3e5a","#4a7c59","#7c4a6b","#7c5a2d","#2d6b7c","#5a2d7c","#7c2d2d","#4a4a7c"];
function getTripColor(id){var h=0;for(var i=0;i<id.length;i++)h=(h*31+id.charCodeAt(i))&0xffffffff;return COVER_COLORS[Math.abs(h)%COVER_COLORS.length];}

function resizeCoverImage(file){
  return new Promise(function(resolve){
    if(file.size>5*1024*1024){toast("写真は5MB以内にしてください");resolve(null);return;}
    var img=new Image();var url=URL.createObjectURL(file);
    img.onload=function(){
      var MW=1200,MH=630,w=img.width,h=img.height;
      if(w>MW){h=Math.round(h*MW/w);w=MW;}
      if(h>MH){w=Math.round(w*MH/h);h=MH;}
      var canvas=document.createElement("canvas");canvas.width=w;canvas.height=h;
      canvas.getContext("2d").drawImage(img,0,0,w,h);
      URL.revokeObjectURL(url);
      canvas.toBlob(function(blob){resolve(blob);},"image/jpeg",0.8);
    };
    img.onerror=function(){URL.revokeObjectURL(url);resolve(null);};
    img.src=url;
  });
}

async function uploadCoverPhoto(file){
  if(isGuest){toast("💡 保存するにはログインが必要です");return;}
  if(!storage){toast("ストレージが利用できません");return;}
  var blob=await resizeCoverImage(file);if(!blob)return;
  var sel=getSel();if(!sel)return;
  toast("アップロード中...");
  try{
    var path="users/"+user.uid+"/covers/"+sel.id+".jpg";
    var ref=storage.ref(path);
    await ref.put(blob,{contentType:"image/jpeg"});
    var url=await ref.getDownloadURL();
    await upd({coverUrl:url});
    toast("カバー写真を設定しました");
  }catch(e){toast("アップロード失敗: "+e.message);}
}
```

- [ ] **Step 2: 構文エラーがないことを確認する**

ブラウザでページをリロードし、コンソールにJS構文エラーが出ないことを確認する。

- [ ] **Step 3: コミットする**

```bash
git add index.html
git commit -m "feat: add getTripColor, resizeCoverImage, uploadCoverPhoto helpers"
```

---

### Task 3: renderList() — カードにカバー写真エリアを追加

**Files:**
- Modify: `index.html` — `renderList()` 関数（line 623付近）

- [ ] **Step 1: `renderList()` 内のカード生成部分を変更する**

現在の `var card=ce("div","trip-card",...)` の行（line 631付近）の直後に、カバーエリアの挿入コードを追加する。

**変更前（line 631〜632付近）:**
```js
    var card=ce("div","trip-card",{onclick:function(){selId=trip.id;activeTab="itinerary";view="detail";showMap=false;render();}});
    if(trip.ownerId===user.uid){var delBtn=...
```

**変更後:**
```js
    var hasCover=!!trip.coverUrl;
    var card=ce("div","trip-card"+(hasCover?" has-cover":""),{onclick:function(){selId=trip.id;activeTab="itinerary";view="detail";showMap=false;render();}});
    var covWrap=ce("div","trip-card-cover-wrap",{onclick:function(e){e.stopPropagation();}});
    if(hasCover){
      var covImg=document.createElement("img");covImg.className="trip-card-cover-img";covImg.src=trip.coverUrl;ap(covWrap,covImg);
    }else{
      covWrap.style.background=getTripColor(trip.id);
    }
    if(!isViewOnly&&!isGuest&&user&&trip.ownerId===user.uid){
      var covBtn=ce("button","trip-card-cover-btn",{onclick:function(e){e.stopPropagation();var fi=document.createElement("input");fi.type="file";fi.accept="image/*";fi.onchange=function(ev){var f=ev.target.files[0];if(f){selId=trip.id;uploadCoverPhoto(f);}};fi.click();}});
      ap(covBtn,tx("📷"));ap(covWrap,covBtn);
    }
    ap(card,covWrap);
    if(trip.ownerId===user.uid){var delBtn=...
```

- [ ] **Step 2: ブラウザで確認する**

1. ログイン状態で旅行一覧を開く
2. 各カード上部に単色プレースホルダーが表示されることを確認
3. カード上の📷ボタンで写真を選択 → アップロード → 写真が表示されることを確認
4. スマホ幅でもレイアウトが崩れないことを確認
5. コンソールにエラーが出ないことを確認

- [ ] **Step 3: コミットする**

```bash
git add index.html
git commit -m "feat: add cover photo area to trip cards in renderList"
```

---

### Task 4: renderDetail() — hero エリアにカバー写真を追加

**Files:**
- Modify: `index.html` — `renderDetail()` 関数（line 664付近）

- [ ] **Step 1: `renderDetail()` の hero 部分を変更する**

**変更前（line 665〜670付近）:**
```js
  var sel=getSel();if(!sel)return ce("div","");var wrap=ce("div","");
  var hero=ce("div","hero");var hm=ce("div","hero-meta");
  if(sel.destination)ap(hm,ap(ce("span",""),tx(" "+sel.destination)));
  if(sel.startDate){ap(hm,ap(ce("span",""),tx(sel.startDate+(sel.endDate?" → "+sel.endDate:""))));ap(hm,ap(ce("span","pill"),tx(getDaysLeft(sel.startDate))));}
  if((sel.memberIds&&sel.memberIds.length||0)>1)ap(hm,ap(ce("span",""),tx("👥 "+(sel.memberIds.length)+"人で共有中")));
  ap(hero,hm);ap(wrap,hero);
```

**変更後:**
```js
  var sel=getSel();if(!sel)return ce("div","");var wrap=ce("div","");
  var hero=ce("div","hero");
  var covW=ce("div","hero-cover-wrap");
  if(sel.coverUrl){
    var cImg=document.createElement("img");cImg.className="hero-cover-img";cImg.src=sel.coverUrl;ap(covW,cImg);
  }else{
    var cPh=ce("div","hero-cover-placeholder");cPh.style.background=getTripColor(sel.id);ap(covW,cPh);
  }
  if(!isViewOnly&&!isGuest&&user&&sel.ownerId===user.uid){
    var cBtn=ce("button","hero-cover-btn",{onclick:function(){var fi=document.createElement("input");fi.type="file";fi.accept="image/*";fi.onchange=function(ev){var f=ev.target.files[0];if(f)uploadCoverPhoto(f);};fi.click();}});
    ap(cBtn,tx("📷 カバーを変更"));ap(covW,cBtn);
  }
  ap(hero,covW);
  var hm=ce("div","hero-meta");
  if(sel.destination)ap(hm,ap(ce("span",""),tx(" "+sel.destination)));
  if(sel.startDate){ap(hm,ap(ce("span",""),tx(sel.startDate+(sel.endDate?" → "+sel.endDate:""))));ap(hm,ap(ce("span","pill"),tx(getDaysLeft(sel.startDate))));}
  if((sel.memberIds&&sel.memberIds.length||0)>1)ap(hm,ap(ce("span",""),tx("👥 "+(sel.memberIds.length)+"人で共有中")));
  ap(hero,hm);ap(wrap,hero);
```

- [ ] **Step 2: ブラウザで確認する**

1. 旅行詳細を開いて hero エリアにカバー写真（またはプレースホルダー色）が表示されることを確認
2. 「📷 カバーを変更」ボタンで写真をアップロードできることを確認
3. アップロード後、カード一覧と詳細の両方に写真が反映されることを確認
4. isViewOnly（共有リンク閲覧）時に 📷 ボタンが表示されないことを確認
5. ゲストモードで 📷 ボタンが表示されないことを確認

- [ ] **Step 3: コミットしてデプロイする**

```bash
git add index.html
git commit -m "feat: add cover photo to trip detail hero area"
git push origin main
```
