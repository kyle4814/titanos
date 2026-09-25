---
name: titanos-git-identity
description: This host has no git user.name/email; commit with per-command -c identity kyle4814 <tech2scale@gmail.com>
metadata:
  node_type: memory
  type: reference
  originSessionId: 14488c11-4b76-44ab-9156-4cb09b326a3a
  modified: 2026-09-25T10:17:22.657Z
---

The UserLAnd host at /home/userland/titanos has no git identity configured, so a plain `git commit` fails with "Author identity unknown". Every commit in the repo is authored `kyle4814 <tech2scale@gmail.com>`. When Kyle has authorized a commit, use `git -c user.name=kyle4814 -c user.email=tech2scale@gmail.com commit ...` rather than writing git config. Remote: github.com/kyle4814/titanos (public), branch master.
