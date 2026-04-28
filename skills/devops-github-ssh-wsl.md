---
name: github-ssh-wsl
description: WSL 环境连接 GitHub SSH 的排障——22端口被封时走443（HTTPS-over-SSH），以及推送时权限错误的修复
tags: [github, ssh, wsl, firewall, 排障]
---

# GitHub SSH + WSL 排障指南

## 两种堵法与应对

### 场景A：22端口封，443通（文档主要场景）
```bash
# 用 ssh config 走 443
ssh -T -p 443 git@ssh.github.com  # 认证成功即OK
git clone "ssh://git@ssh.github.com:443/username/repo.git"
```

### 场景B：443端口封，22端口通（今天遇到）
```bash
# 直接用 git@ 格式克隆即可，无需任何 SSH config
git clone git@github.com:username/repo.git
# 验证：ssh -T git@github.com 成功即OK
```

**判断方法：**
```bash
# 测443（HTTPS）
curl -s --connect-timeout 5 https://github.com 2>&1 | head -3

# 测22（SSH）
ssh -T -o ConnectTimeout=10 -o StrictHostKeyChecking=no git@github.com 2>&1

# 两个都失败 → 网络问题
# 443失败但22成功 → 场景B，直接用 git@ 格式
# 22失败但443成功 → 场景A，用上述 ssh config 方法
```

## 问题症状

```bash
# 症状1：克隆/推送时 connection refused
ssh: connect to host github.com port 22: Connection refused

# 症状2：认证成功但 read-only
Authenticated, but GitHub does not provide shell access.
# 或
Permission denied (publickey).
```

---

## 根因

WSL 的 22 端口被 Windows 防火墙封了，但 443 端口（HTTPS）可以通。

---

## 修复步骤

### 1. 创建 SSH 配置文件（走 443 端口）

```bash
cat > ~/.ssh/config << 'EOF'
Host github.com
    Hostname ssh.github.com
    Port 443
    User git
EOF
chmod 600 ~/.ssh/config
```

### 2. 生成 SSH Key（如果还没有）

```bash
ssh-keygen -t ed25519 -C "your-email@example.com" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
# 把公钥添加到 GitHub Settings → SSH Keys
```

### 3. 验证连通性

```bash
ssh -T -o StrictHostKeyChecking=no -p 443 git@ssh.github.com
# 期望输出：Hi xxx! You've successfully authenticated...
```

### 4. 如果 clone/push 仍然失败——用完整 SSH URL 格式

SSH config 的 `Host github.com` 映射在远程 URL 是 `git@github.com:` 格式时可能不生效，需要显式指定：

```bash
# 克隆时用完整格式
git clone "ssh://git@ssh.github.com:443/username/repo.git"

# 已有仓库改 remote URL
cd your-repo
git remote set-url origin "ssh://git@ssh.github.com:443/username/repo.git"
git push origin main
```

### 5. 推送时报 "Permission denied (publickey)" 或 "read only"

即使 `ssh -T` 认证成功，**git push 仍失败**的可能原因：

**原因A：Deploy Key 是 read-only**
1. 打开 `https://github.com/username/repo/settings/keys`
2. 找到该 SSH Key → **Edit**
3. 勾选 **"Allow write access"**
4. 保存

**原因B：remote URL 格式问题**
```bash
# 当前格式（可能不生效）
git remote -v
# 输出: origin  git@github.com:username/repo.git (fetch)

# 改为完整格式（强制走443）
git remote set-url origin "ssh://git@ssh.github.com:443/username/repo.git"

# 验证
git remote -v
# 应输出: origin  ssh://git@ssh.github.com:443/username/repo.git (fetch)

# 现在推送
git push origin main
```

### 6. 快速验证链路是否全通

```bash
# 完整路径测试（不走 git@github.com 简写）
ssh -v -T -o StrictHostKeyChecking=no -p 443 git@ssh.github.com 2>&1 | grep -E "(Authenticat|Accepted|shell access)"
# 期望: Authentication succeeded + "shell access" 消息

# git 协议测试
GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=no -p 443" git ls-remote git@github.com:username/repo.git
```

---

## 推送完整流程

```bash
# 1. 克隆仓库
git clone git@github.com:username/repo.git
cd repo

# 2. 验证 SSH（走443）
ssh -T -p 443 git@ssh.github.com

# 3. 如果失败，改 remote URL
git remote set-url origin "ssh://git@ssh.github.com:443/username/repo.git"

# 4. 推送
git push origin main
```

---

## 验证命令汇总

| 目的 | 命令 |
|------|------|
| 测试 SSH 认证 | `ssh -T -p 443 git@ssh.github.com` |
| 查看 remote URL | `git remote -v` |
| 改用 443 SSH | `git remote set-url origin "ssh://git@ssh.github.com:443/user/repo.git"` |
| 查看 SSH config | `cat ~/.ssh/config` |

---

## Pitfalls

1. **SSH config 的 Host 映射只对 `github.com` 主机名生效**：`git@github.com:` 会走 config，但 `ssh://git@ssh.github.com:443/` 绕过了 config 的 Host 字段，需要用 `git remote set-url` 改掉 remote URL
2. **Deploy Key 默认只读**：在仓库 Settings → Keys 里必须手动勾选 "Allow write access"
3. **443 端口走的是 HTTPS-over-SSH tunnel**：不是直连 TCP 22，是 HTTP-like 的 tunnel，ssh config 的 Host 映射对它不生效
4. **`ssh -T` 成功不等于 git push 成功**：deploy key 可能 read-only，或者 remote URL 没走 443
