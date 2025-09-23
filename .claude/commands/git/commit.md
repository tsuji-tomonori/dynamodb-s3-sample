---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git commit:*)
description: ai-netリポジトリ用のコミット作成（.gitmessageテンプレート使用）
argument-hint: [type] [scope] [subject]
---

## コンテキスト

- 現在のgitステータス: !`git status`
- 変更内容（staged/unstaged）: !`git diff HEAD`
- 現在のブランチ: !`git branch --show-current`
- 最近のコミット: !`git log --oneline -5`

## コミットメッセージテンプレート

@.gitmessage を参照

## タスク

1. 上記の変更内容を確認
2. .gitmessageテンプレートに従ってコミットメッセージを作成
3. 必要なファイルをgit addでステージング
4. git commitでコミットを日本語で作成

引数が指定された場合: $ARGUMENTS
