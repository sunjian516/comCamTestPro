# Hermes Agent 备份与恢复指南

> 如果你的电脑坏了，在新电脑上恢复 Hermes Agent 的所有记忆、配置和技能。

---

## 备份包含什么

| 内容 | 说明 |
|------|------|
| `~/.hermes/` | 记忆、配置、技能、定时任务、会话历史 |
| `~/.ssh/` | SSH Key（用于 GitHub 推送） |

---

## 备份文件

```
hermes_backup_YYYYMMDD.tar.gz
```

---

## 新电脑恢复步骤

### 第一步：安装 Hermes Agent

按原来方式在新电脑安装 Hermes Agent（略）。

### 第二步：获取备份文件

从 GitHub 下载备份：

```bash
# 克隆仓库
git clone git@github.com:sunjian516/comCamTestPro.git hermes_restore
cd hermes_restore

# 找到最新的备份文件（日期最大的）
ls -lh hermes_backup_*.tar.gz
```

### 第三步：解压覆盖

```bash
# 解压到用户目录（会自动覆盖 .hermes 和 .ssh）
tar -xzvf hermes_backup_YYYYMMDD.tar.gz -d ~/

# 重启 Hermes Agent（具体命令看你怎么启动的）
```

### 第四步：验证恢复

```bash
# 检查记忆是否恢复
cat ~/.hermes/memories/MEMORY.md

# 检查 SSH Key
ls -la ~/.ssh/

# 重启 hermes-agent 后，对我说"你好"测试一下
```

---

## 定期备份（可选）

在你当前的电脑上，随时可以生成新备份：

```bash
# 在 WSL 里执行
tar -czvf ~/hermes_backup_$(date +%Y%m%d).tar.gz -C /home/dministrator .hermes .ssh

# 然后推送到 GitHub（需要先从仓库克隆）
git clone git@github.com:sunjian516/comCamTestPro.git hermes_restore
cd hermes_restore
cp ~/hermes_backup_YYYYMMDD.tar.gz .
git add hermes_backup_YYYYMMDD.tar.gz
git commit -m "Hermes backup YYYYMMDD"
git push
```

---

## 注意事项

- 备份包含**所有对话历史和记忆**，请妥善保管备份文件
- 如果 GitHub SSH Key 权限是 **Read-only**，需要手动在网页改成 **Read/Write** 才能推送
- 备份不包含大型模型文件（如果有）和临时下载文件
