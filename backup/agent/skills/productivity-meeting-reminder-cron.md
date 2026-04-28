---
name: meeting-reminder-cron
description: 机电信息保障部会议提醒定时任务管理——每周日接收PDF后提取会议信息、更新Cronjob，支持动态日期、天气、参会人员
tags: [cron, meeting, reminder, wechat, 机电保障部]
---

# 会议提醒 Cronjob 管理

## 核心规则（5条）

1. **每周日收到PDF** → 我提取会议信息、更新数据文件，微信发一周总体预览
2. **每周日第一次收到PDF后** → 微信输出一次一周总体日程安排
3. **每天早上7点** → 微信发当天会议安排（仅正式会议，不发个人行程）
4. **每天会议前30分钟** → 微信提醒下一个会议
5. **其余时间** → 不主动提醒，不打扰休息

---

## 第一步：从PDF提取文本

```python
import fitz  # PyMuPDF

pdf_path = "/path/to/机电一周...pdf"
doc = fitz.open(pdf_path)

for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text()
    print(f"=== 第 {page_num+1} 页 ===")
    print(text)
```

重点关注PDF最后一页的**机电信息保障部一周会议安排**表格，这是结构化数据。

---

## 会议数据持久化

所有cronjob共享同一个数据文件：`/home/dministrator/.hermes/data/meetings_latest.txt`

格式：Python 7元素元组数组文本
```
[(0, "09:00", "华山医院体检", "华山医院", "个人行程", "-", "个人"),
 (1, "14:00", "碰头会", "588号", "徐波、胡怡斌、王萍、戴艳、尹洁", "既定范围", "会议"),
 ...
]
```

收到新PDF后：
1. 用 PyMuPDF 提取文本
2. 解析会议数据
3. **覆盖写入** meetings_latest.txt
4. 微信发送一周预览（模式A）

从PDF提取以下字段：

| 字段 | 来源 | 示例 |
|------|------|------|
| 星期 | PDF第一列 | 周一、周二... |
| 时间 | PDF | 16:00、09:00、下午 |
| 会议名称 | PDF | 碰头会、T2航显系统... |
| 地点 | PDF | 588号、302会议室、闵行区委党校 |
| 出席人员 | PDF（出席领导列） | 徐波、戴艳、尹洁 |
| 参加范围 | PDF（参加范围列） | 业务管理部、系统运行部... |

**注意**：全面从严治党参观只有"下午"，无精确时间，视为14:00处理。

---

## 第三步：更新 Cronjob

用 `cronjob(action='update', job_id='d1cb974cdfd2', prompt='...' )` 更新 prompt。

prompt 模板核心结构：

```markdown
## 会议模板（每周重复，时间固定）

> ⚠️ 注意：Python代码中 meetings 列表每个条目为 7 元素元组：
> `(day_idx, time, name, location, attendees, scope, type)`
> - day_idx: 0=周一, 1=周二, ... 6=周日
> - type: "会议" 或 "个人"
> **所有条目必须统一为 7 元素，缺失字段用 "-" 填充**

| 星期 | 时间 | 会议名称 | 地点 | 出席人员 | 参加范围 | 类型 |
|------|------|----------|------|----------|----------|------|
| 周一 | 16:00 | 碰头会 | 588号 | 徐波、胡怡斌、王萍、戴艳、尹洁 | 既定范围 | 会议 |
| ... | ... | ... | ... | ... | ... |

## 当前日期计算
用 Python 计算当前周周一/周日，动态生成会议日期

## 提醒逻辑
1. 获取当前时间
2. 遍历本周所有会议，计算30分钟触发时间
3. 判断当前时间是否在触发时间±2分钟内
4. 过滤已过的会议
5. 只发送一次（检查日志）

## 发送格式（含天气和人员）
- 普通：地点不含"588"
- 588号：curl wttr.in 获取上海虹桥机场天气
```

---

## 关键坑点

1. **日期写死**：prompt 里不要写死日期（04/20-04/24），每周日期不同，必须用 Python 动态计算
2. **过滤已过期**：检查时先判断当前时间 > 会议开始时间，跳过
4. **防止重复发送**：发送前查日志 `/home/dministrator/.hermes/data/meeting_reminders_log.txt`（注意不是 `~/.hermes/data/...`，实际路径在 dministrator 用户目录下）
5. **个人行程不提醒**：类型为"个人"的会议（如华山医院体检）只展示在日程中，不发微信提醒
6. **碰头会16:00**：提醒触发时间为 15:30（提前30分钟）
7. **五一假期（周五全天）**：无任何会议，不发提醒
8. **隐私保护**：参会人员信息仅用于提醒格式，不得他用
9. **首次确认**：收到新PDF后，先提取周一会议展示给用户确认，再更新cronjob

---

## job_id（实际运行）

| 任务 | job_id | 频率 | 用途 |
|------|--------|------|------|
| 会议30分钟前提醒 | `04da028ba614` | `*/5 * * * *` | 每次会议前30分钟微信提醒 |
| 每日7点当天日程 | `f1ae19e52181` | `0 7 * * *` | 每天早上7点发当天会议安排 |
| GitHub备份 | `5cbc9ee8d344` | `0 23 * * 0` | 每周日备份 |

WeChat chat_id：`o9cq804Yq-r837AH5C_ou5qzp_kg@im.wechat`

## 实际发送代码（2026-04-27验证有效）

xurl CLI 未安装，必须通过 Hermes WeChat 网关发送。使用 `execute_code` 工具运行以下代码：

```python
import sys, os, asyncio
sys.path.insert(0, '/home/dministrator/projects/hermes-agent')
os.chdir('/home/dministrator/projects/hermes-agent')
import gateway.platforms.weixin as wx
import json

accounts_dir = "/home/dministrator/.hermes/weixin/accounts"
bot_creds = []
for f in os.listdir(accounts_dir):
    if f.endswith("@im.bot.json"):
        path = os.path.join(accounts_dir, f)
        with open(path) as fp:
            data = json.load(fp)
        bot_creds.append({
            "account_id": data.get('user_id', '').split('@')[0],
            "token": data.get('token', ''),
            "wechat_user_id": data.get('user_id', '')
        })

chat_id = "o9cq804Yq-r837AH5C_ou5qzp_kg@im.wechat"

def build_msg(meeting):
    return f"""📋 会议提醒【今日 {meeting['time']}】

🏷 名称：{meeting['name']}
📍 地点：{meeting['location']}
👤 出席：{meeting['attendees']}
📌 范围：{meeting['scope']}
⏰ 时间：今日 {meeting['time']}（提前30分钟提醒）

请相关人员准时参加。"""

async def send_reminders(meetings_to_remind):
    for creds in bot_creds:
        try:
            for m in meetings_to_remind:
                await wx.send_weixin_direct(
                    token=creds["token"],
                    extra={"account_id": creds["account_id"]},
                    chat_id=chat_id,
                    message=build_msg(m),
                    media_files=[]
                )
            return True
        except Exception as e:
            print(f"Failed with {creds['account_id']}: {e}")
    return False

# 填入需要提醒的会议（见上方模板）
meetings = []
asyncio.run(send_reminders(meetings))
```

### 关键坑

1. **xurl CLI 未安装**：cron prompt 引用 xurl skill 但机器上没有，运行时必须改用 send_weixin_direct
2. **必须用 execute_code**：不能用 `send_message` 工具，会报错 `"Timeout context manager should be used inside a task"`
3. **bot credentials 在 `~/.hermes/weixin/accounts/*.json`**：遍历尝试，session timeout 时换另一个 bot
4. **30分钟窗口判断**：cron `*/5 * * * *`，筛选 会议时间-当前时间 ∈ [30, 35] 分钟 的会议，只发"会议"类型，跳过"个人"类型

### 两种提醒模式

#### 模式A：每周预览（推荐周日/周一发送）
一次性发送本周所有后续会议，按日期分组，不做30分钟窗口判断：

```python
from datetime import datetime, timedelta
from itertools import groupby

now = datetime.now()
today = now.date()
today_weekday = today.weekday()  # 0=Mon
day_names = ['周一','周二','周三','周四','周五','周六','周日']

# 会议模板 (day_idx, time, name, location, attendees, scope, type)
meetings = [
    # day_idx: 0=周一, 1=周二, ..., 6=周日
    # type: "会议" 或 "个人"
    # 缺失字段用 "-" 填充，确保每行都是 7 元素
    (0, "09:00", "华山医院体检", "华山医院", "个人行程", "-", "个人"),
    ...
]
# 过滤：已过日期跳过，当天未过的会议保留
upcoming = []
for m in meetings:
    day_idx, time_str, name, loc, attendees, scope, mtype = m
    mt = datetime.strptime(time_str, "%H:%M").time()
    if day_idx > today_weekday:
        conf_date = today + timedelta(days=day_idx - today_weekday)
        upcoming.append((day_idx, time_str, name, loc, attendees, mtype, conf_date))
    elif day_idx == today_weekday and now.time() < mt:
        upcoming.append((day_idx, time_str, name, loc, attendees, mtype, today))

# 按日期分组
groups = {}
for m in upcoming:
    groups.setdefault(m[0], []).append(m)

msg_lines = [
    f"📅 机电信息保障部本周会议提醒",
    f"🕐 生成时间: {now.strftime('%Y-%m-%d %H:%M')}",
    f"📆 本周区间: {today.strftime('%Y.%m.%d')} ~ {(today+timedelta(days=6)).strftime('%Y.%m.%d')} (周一~周日)",
    "",
    "⚠️ 如有变化，请以最新PDF日程安排为准",
    "",
    "─" * 40,
]
for day_idx in sorted(groups.keys()):
    day_meetings = groups[day_idx]
    first_date = day_meetings[0][6]
    msg_lines.append(f"\n🗓 {day_names[day_idx]}（{first_date.strftime('%m月%d日')}）")
    msg_lines.append("─" * 40)
    for m in day_meetings:
        _, time_str, name, loc, attendees, mtype, _ = m
        emoji = "📌" if mtype == "会议" else "🏥"
        msg_lines.append(f"{emoji} {time_str} {name}")
        if loc != "-":
            msg_lines.append(f"   📍 地点: {loc}")
        if attendees != "-":
            main = attendees.split("（")[0]
            msg_lines.append(f"   👤 出席: {main}")

msg = "\n".join(msg_lines)
```

#### 模式B：逐个30分钟触发提醒（cron `*/5 * * * *`用）
每5分钟检查一次，发送即将在30分钟后开始的单个会议提醒，格式见上方 `build_msg(meeting)` 函数。
