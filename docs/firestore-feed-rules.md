# Firestore セキュリティルール / インデックス（タイムライン機能）

タイムライン機能（`feed` コレクション）を有効にするには、Firebase コンソールで以下のセキュリティルールとインデックスを設定する必要がある。これはコードのデプロイ（静的サイトの公開）とは**別の手動作業**。これを行うまで `feed` の読み書きは `permission-denied` になる。

## セキュリティルール

Firebase コンソール → Firestore Database → ルール に、既存の `trips` / `users` ルールを残したまま、以下の `feed` ブロックを追加して「公開」する。

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
        allow create: if request.auth != null && request.auth.uid == uid
          && uid == request.resource.data.uid;
        allow delete: if request.auth != null && request.auth.uid == uid;
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

### ルールの意図

- `feed/{tripId}`
  - **read: 全員** … 未ログインでもタイムラインを閲覧できる（集客）。`feed` は公開してよい項目だけを複製したスナップショットで、メール・会員IDは含まない。
  - **create / delete: オーナーのみ** … 公開・公開停止は本人だけ。
  - **update** … 本人は全項目更新可（再同期）。他人はいいね・コメントのカウンタ（`likeCount`/`commentCount`）の変更だけ許可。これによりログインユーザーが他人の投稿にいいね/コメントしてもカウンタは更新できるが、本文等は改ざんできない。
- `likes/{uid}` … ドキュメントIDをユーザーUIDにして重複いいねを防止。本人のUIDと一致する場合のみ作成・削除可。`uid` フィールドは `loadMyLikes` の collectionGroup クエリで使用。
- `comments/{cid}` … 閲覧は全員。投稿はログイン済みかつ `uid` が本人で、本文が1〜500文字の文字列の場合のみ。削除は本人のみ。

## 複合インデックス

コンソール → Firestore Database → インデックス で以下を作成（アプリ実行時に必要リンクが提示される場合はそこからでも可）。

1. **コレクション `feed`**: `ownerId`（昇順）＋ `publishedAt`（降順）
   - 用途: ユーザー公開プロフィール画面（`where("ownerId","==",uid).orderBy("publishedAt","desc")`）
2. **コレクショングループ `likes`**: `uid`（昇順）
   - 用途: ログインユーザーのいいね状態取得（`collectionGroup("likes").where("uid","==",user.uid)`）

タイムライン本体（`feed` を `publishedAt` 単独降順）は単一フィールドインデックスで自動対応されるため、追加作成は不要。

## 動作確認チェックリスト

- [ ] 別アカウント（または未ログイン）でタイムラインが読める
- [ ] 他人の `feed` ドキュメントの本文等を直接編集できない（オーナー以外は `likeCount`/`commentCount` 以外不可）
- [ ] いいね・コメントが書け、他人のコメントは削除できない
- [ ] 公開プロフィールのクエリがインデックスエラー（`FAILED_PRECONDITION`）にならない
