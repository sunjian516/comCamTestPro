# 知行（Agent）配置备份

本目录存储孙剑的知行 Agent 完整配置，用于系统重装或换电脑后的完整恢复。

---

## 备份内容

| 文件/目录 | 说明 | 是否必须 |
|-----------|------|----------|
| `agent/MEMORY.md` | Agent 持久记忆（环境信息、工具习惯、知识库路径等） | ✅ 必需 |
| `agent/USER.md` | 用户画像（姓名、职位、偏好、沟通方式） | ✅ 必需 |
| `agent/SOUL.md` | Agent 灵魂配置 | ✅ 必需 |
| `agent/jobs.json` | Cron 定时任务配置 | ✅ 必需 |
| `agent/skills/*.md` | 核心技能定义文件 | ✅ 必需 |

> ⚠️ **私密数据（不入库）**：会议日程（meetings_latest.txt）、提醒日志（meeting_reminders_log.txt）等私密日程数据不会上传。

---

## 恢复步骤

### 第一步：安装 Hermes Agent
```bash
# 克隆仓库
git clone https://github.com/sunjian516/comCamTestPro.git
cd comCamTestPro
```

### 第二步：恢复配置
```bash
HERMES_DIR="$HOME/.hermes"

# 恢复记忆和用户配置
cp backup/agent/MEMORY.md "$HERMES_DIR/memories/"
cp backup/agent/USER.md "$HERMES_DIR/memories/"

# 恢复 SOUL 配置
cp backup/agent/SOUL.md "$HERMES_DIR/"

# 恢复 Cron 任务
cp backup/agent/jobs.json "$HERMES_DIR/cron/"

# 恢复技能定义（按目录结构放回）
SKILLS_DIR="$HERMES_DIR/skills/productivity"
mkdir -p "$SKILLS_DIR"
cp backup/agent/skills/productivity-meeting-reminder-cron.md "$SKILLS_DIR/meeting-reminder-cron/SKILL.md"
```

### 第三步：重启 Agent
```bash
# 重启 Hermes gateway
```

---

## 备份记录

| 时间 | 内容说明 |
|------|----------|
| 2026-04-28 10:00 | 首次完整备份：MEMORY.md、USER.md、SOUL.md、jobs.json、skills（含会议提醒、绩效考核、GitHub认证等核心技能） |

---

## 注意事项

1. **私密日程不过库**：每次备份时，`meetings_latest.txt` 和 `meeting_reminders_log.txt` 明确排除在外
2. **恢复后需重新验证**：部分配置（如 WeChat Token、GitHub SSH Key）可能需要重新授权
3. **技能目录结构**：skills 文件恢复时需按 `category/skill-name/SKILL.md` 结构放置

---
