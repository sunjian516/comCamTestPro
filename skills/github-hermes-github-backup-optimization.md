---
name: hermes-github-backup-optimization
description: WSL2下GitHub推送极慢（443超时）的解决方案：SSH克隆、极致压缩9、大文件排除、选择性备份非私密配置
tags: [github, backup, wsl2, ssh, performance]
---

# Hermes GitHub 备份优化

## 背景
WSL2 环境访问 GitHub 极慢，443 端口连接超时，需要特殊配置才能正常推送。

## 核心问题
Git push 超时（timeout），即使文件很小也推不上去。

## 解决方案

### 1. SSH 方式克隆（推荐）
```bash
git clone git@github.com:sunjian516/comCamTestPro.git
```
SSH 方式比 HTTPS 稳定，不会被 443 端口阻塞。

### 2. 启用极致压缩
```bash
git config core.compression 9
```
加速网络传输，对小文件效果显著。

### 3. 大文件处理
如果仓库里有 >10MB 的文件（如 tar.gz 备份包），会严重拖累推送。
**解决**：删除大文件，只备份纯文本配置。

## 备份策略（最终版）

### 只备份非私密配置
```
✅ 备份：MEMORY.md, USER.md, SOUL.md, jobs.json, skills/*.md
❌ 不备份：meetings_latest.txt（私密日程）, *.tar.gz（大文件）
```

### 每次备份更新 README 记录
在 README.md 的备份记录表格追加一行。

## 仓库结构
```
comCamTestPro/
├── README.md
├── MEMORY.md
├── USER.md
├── SOUL.md
├── jobs.json
└── skills/
    └── *.md
```

## 备份命令模板
```bash
REPO_DIR="$HOME/projects/comCamTestPro"
cd "$REPO_DIR"
git add -A
git commit -m "🤖 每周备份 $(date '+%Y-%m-%d %H:%M')"
git config core.compression 9
git push
```
