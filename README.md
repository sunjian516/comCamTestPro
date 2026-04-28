# 知行 Agent 配置备份

本仓库用于存储孙剑的**知行（Agent）**完整配置，实现系统重装或换电脑后的完整恢复。

---

## 目录结构

```
comCamTestPro/
├── README.md          # 本文件
├── MEMORY.md          # Agent 持久记忆
├── USER.md            # 用户画像
├── SOUL.md            # 灵魂配置
├── jobs.json          # Cron 定时任务配置
└── skills/             # 核心技能定义
    ├── productivity-meeting-reminder-cron.md
    ├── productivity-system-operations-weekly-report.md
    ├── github-github-auth.md
    └── github-github-repo-management.md
```

---

## 一、安装 Hermes Agent（从零开始）

### 第一步：环境准备

```bash
# 确认系统环境（Windows 10/11 + WSL2）
wsl --list --verbose
# 确保 WSL2 已安装，Ubuntu 版本

# 更新系统
sudo apt update && sudo apt upgrade -y
```

### 第二步：安装 Hermes Agent

```bash
# 克隆 Hermes Agent 主仓库
git clone https://github.com/NousResearch/hermes-agent.git ~/projects/hermes-agent

# 或者使用 SSH（如果配置了SSH Key）
git clone git@github.com:NousResearch/hermes-agent.git ~/projects/hermes-agent

cd ~/projects/hermes-agent
```

### 第三步：配置 Python 环境

```bash
# 确认 Python 版本 >= 3.10
python3 --version

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -e .
```

### 第四步：配置 Hermes

```bash
# 初始化配置目录
mkdir -p ~/.hermes

# 复制示例配置
cp ~/projects/hermes-agent/config.yaml.example ~/.hermes/config.yaml

# 编辑配置（填入 API Key 等敏感信息）
nano ~/.hermes/config.yaml
```

### 第五步：启动 Gateway

```bash
# 启动 Hermes Gateway
hermes gateway

# 或使用 nohup 后台运行
nohup hermes gateway > ~/.hermes/logs/gateway.log 2>&1 &
```

---

## 二、配置 WeChat 连接

```bash
# 在 WeChat 中搜索 Hermes Bot 并添加
# 获取 Bot 的 Token 并填入 config.yaml
```

---

## 三、恢复备份配置

### 第一步：拉取备份仓库

```bash
# 克隆本仓库
git clone git@github.com:sunjian516/comCamTestPro.git ~/projects/comCamTestPro

cd ~/projects/comCamTestPro
```

### 第二步：恢复核心配置

```bash
HERMES_DIR="$HOME/.hermes"
BACKUP_DIR="$HOME/projects/comCamTestPro"

# 创建必要目录
mkdir -p "$HERMES_DIR/memories"
mkdir -p "$HERMES_DIR/skills/productivity"
mkdir -p "$HERMES_DIR/skills/github"

# 恢复记忆和用户配置
cp "$BACKUP_DIR/MEMORY.md" "$HERMES_DIR/memories/"
cp "$BACKUP_DIR/USER.md" "$HERMES_DIR/memories/"

# 恢复 SOUL 配置
cp "$BACKUP_DIR/SOUL.md" "$HERMES_DIR/"

# 恢复 Cron 任务
cp "$BACKUP_DIR/jobs.json" "$HERMES_DIR/cron/"
```

### 第三步：恢复技能定义

```bash
# 恢复会议提醒技能
mkdir -p "$HERMES_DIR/skills/productivity/meeting-reminder-cron"
cp "$BACKUP_DIR/skills/productivity-meeting-reminder-cron.md" \
   "$HERMES_DIR/skills/productivity/meeting-reminder-cron/SKILL.md"

# 恢复绩效考核技能
mkdir -p "$HERMES_DIR/skills/productivity/system-operations-weekly-report"
cp "$BACKUP_DIR/skills/productivity-system-operations-weekly-report.md" \
   "$HERMES_DIR/skills/productivity/system-operations-weekly-report/SKILL.md"

# 恢复 GitHub 认证技能
mkdir -p "$HERMES_DIR/skills/github/github-auth"
cp "$BACKUP_DIR/skills/github-github-auth.md" \
   "$HERMES_DIR/skills/github/github-auth/SKILL.md"

# 恢复 GitHub 仓库管理技能
mkdir -p "$HERMES_DIR/skills/github/github-repo-management"
cp "$BACKUP_DIR/skills/github-github-repo-management.md" \
   "$HERMES_DIR/skills/github/github-repo-management/SKILL.md"
```

### 第四步：重启 Agent

```bash
# 杀掉旧进程
pkill -f hermes || true

# 重新启动
cd ~/projects/hermes-agent
hermes gateway
```

---

## 四、备份内容说明

| 文件 | 说明 | 是否必需 |
|------|------|----------|
| `MEMORY.md` | Agent 持久记忆：环境信息、工具习惯、知识库路径、用户偏好 | ✅ 必需 |
| `USER.md` | 用户画像：姓名、职位、沟通方式偏好 | ✅ 必需 |
| `SOUL.md` | Agent 灵魂配置：性格、行为准则 | ✅ 必需 |
| `jobs.json` | Cron 定时任务：会议提醒、绩效考核、版本检查 | ✅ 必需 |
| `skills/*.md` | 核心技能定义：会议提醒、绩效考核、GitHub认证 | ✅ 必需 |

> ⚠️ **私密数据（不入库）**：`meetings_latest.txt`（会议日程）、`meeting_reminders_log.txt`（提醒日志）属于私密日程，**永不**上传。

---

## 五、恢复后验证

```bash
# 验证记忆是否加载
hermes status

# 验证 Cron 任务是否恢复
hermes cron list

# 测试会议提醒
hermes cron run 04da028ba614  # 手动触发一次会议提醒测试
```

---

## 备份记录

| 时间 | 内容说明 |
|------|----------|
| 2026-04-28 10:30 | 全量备份：MEMORY、USER、SOUL、jobs.json、**88个技能**全部纳入备份 |

---

## 注意事项

1. **私密日程不过库**：每次备份时，`meetings_latest.txt` 和 `meeting_reminders_log.txt` 明确排除在外
2. **恢复后需重新授权**：WeChat Token、GitHub SSH Key 等凭证需要重新配置
3. **技能目录结构**：skills 文件恢复时需按 `category/skill-name/SKILL.md` 结构放置
4. **每周自动备份**：每周日23点自动执行备份（`5cbc9ee8d344`）

---
