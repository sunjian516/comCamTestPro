---
name: weixin-meeting-reminder
description: 微信会议提醒发送（execute_code版）— 每天7点读取会议数据发送微信
category: productivity
---
# 微信会议提醒发送（execute_code 版）

## 触发条件
1. **每周日收到PDF后** → 提取会议数据，发送一周总体日程安排
2. **每天早上7点** → 发送当天会议安排
3. **会议前30分钟** → 微信提醒下一场会议
4. **其余时间** → 静默，不打扰

## 场景一：每周日收到PDF后（发送一周总体日程）

```python
import sys, os, ast
sys.path.insert(0, '/home/dministrator/projects/hermes-agent')
os.chdir('/home/dministrator/projects/hermes-agent')
import gateway.platforms.weixin as wx
import asyncio
from datetime import datetime

# 读取会议数据
meetings_path = "/home/dministrator/.hermes/data/meetings_latest.txt"
with open(meetings_path) as f:
    meetings = ast.literal_eval(f.read().strip())

weekday_names = ["周一","周二","周三","周四","周五","周六","周日"]

# 过滤出本周会议（周一~周五）
workday_meetings = [m for m in meetings if len(m) >= 7 and m[6] == "会议" and m[0] <= 4]
workday_meetings.sort(key=lambda x: (m[0], m[1]))

# 构造一周总览消息
today = datetime.now()
msg_lines = [f"📅 本周（{today.month}月{today.day}日起）会议总览\n━━━━━━━━━━━━━━━━━━"]

for day_idx in range(5):
    day_name = weekday_names[day_idx]
    day_meetings = [m for m in workday_meetings if m[0] == day_idx]
    if day_meetings:
        msg_lines.append(f"\n{day_name}（{day_name}）：")
        for m in day_meetings:
            _, time_, name, location, attendees, scope, _ = m
            msg_lines.append(f"  ⏰ {time_} {name}")
            msg_lines.append(f"     📍 {location} | 👤 {attendees}")
    else:
        msg_lines.append(f"\n{day_name}：无会议")

msg = "\n".join(msg_lines)

# 发送
account_id = "o9cq804Yq-r837AH5C_ou5qzp_kg@im.wechat"
token = "5221a5d8d221@im.bot:060000d32c32e556453f4d78562bed9db7094c"
chat_id = "o9cq804Yq-r837AH5C_ou5qzp_kg@im.wechat"

async def send():
    await wx.send_weixin_direct(extra={"account_id": account_id}, token=token, chat_id=chat_id, message=msg)

asyncio.run(send())
print("[WEEKLY_SENT]")
```

---

## 场景二：每天早上7点（发送当天日程）

```python
import sys, os, ast
sys.path.insert(0, '/home/dministrator/projects/hermes-agent')
os.chdir('/home/dministrator/projects/hermes-agent')
import gateway.platforms.weixin as wx
import asyncio
from datetime import datetime

log_path = "/home/dministrator/.hermes/data/daily_7am_reminder_log.txt"
today_str = datetime.now().strftime("%Y-%m-%d")
if os.path.exists(log_path):
    with open(log_path) as f:
        if today_str in f.read():
            print("[SILENT]")
            sys.exit(0)

meetings_path = "/home/dministrator/.hermes/data/meetings_latest.txt"
with open(meetings_path) as f:
    meetings = ast.literal_eval(f.read().strip())

today_weekday = datetime.now().weekday()
weekday_names = ["周一","周二","周三","周四","周五","周六","周日"]

today_meetings = [m for m in meetings if m[0] == today_weekday and len(m) >= 7 and m[6] == "会议"]
today_meetings.sort(key=lambda x: x[1])

wname = weekday_names[today_weekday]
month, day = datetime.now().month, datetime.now().day

if not today_meetings:
    print("[NO_MEETINGS]")
    sys.exit(0)

lines = [f"📅 {wname}（{month}月{day}日）\n━━━━━━━━━━━━━━━━━━\n⏰ 今日会议："]
for m in today_meetings:
    _, time_, name, location, attendees, scope, _ = m
    lines.append(f"\n📌 {time_} {name}")
    lines.append(f"   📍 {location} | 👤 {attendees}")
msg = "\n".join(lines)

with open(log_path, "a") as f:
    f.write(today_str + "\n")

account_id = "o9cq804Yq-r837AH5C_ou5qzp_kg@im.wechat"
token = "5221a5d8d221@im.bot:060000d32c32e556453f4d78562bed9db7094c"
chat_id = "o9cq804Yq-r837AH5C_ou5qzp_kg@im.wechat"

async def send():
    await wx.send_weixin_direct(extra={"account_id": account_id}, token=token, chat_id=chat_id, message=msg)

asyncio.run(send())
print("[SENT]")
```

---

## 场景三：会议前30分钟提醒

```python
import sys, os, ast
sys.path.insert(0, '/home/dministrator/projects/hermes-agent')
os.chdir('/home/dministrator/projects/hermes-agent')
import gateway.platforms.weixin as wx
import asyncio
from datetime import datetime, timedelta

log_path = "/home/dministrator/.hermes/data/meeting_30min_log.txt"
now = datetime.now()
today_str = now.strftime("%Y-%m-%d")

meetings_path = "/home/dministrator/.hermes/data/meetings_latest.txt"
with open(meetings_path) as f:
    meetings = ast.literal_eval(f.read().strip())

today_weekday = now.weekday()
today_meetings = [m for m in meetings if m[0] == today_weekday and len(m) >= 7 and m[6] == "会议"]
today_meetings.sort(key=lambda x: x[1])

# 找当前时间~30分钟后的下一场会议
next_meeting = None
for m in today_meetings:
    h, mi = map(int, m[1].split(":"))
    meet_time = now.replace(hour=h, minute=mi, second=0, microsecond=0)
    diff = (meet_time - now).total_seconds()
    if 25 * 60 <= diff <= 35 * 60:  # 25~35分钟内
        next_meeting = m
        break

if not next_meeting:
    print("[NO_IMMINENT]")
    sys.exit(0)

_, time_, name, location, attendees, scope, _ = next_meeting
msg = (f"🔔 会议提醒\n"
       f"━━━━━━━━━━━━━━━━━━\n"
       f"⏰ {time_} - {name}\n"
       f"📍 地点：{location}\n"
       f"👤 出席：{attendees}\n"
       f"━━━━━━━━━━━━━━━━━━\n"
       f"还有30分钟，请准备！")

# 防重复
log_content = today_str + time_ + name
if os.path.exists(log_path):
    with open(log_path) as f:
        if log_content in f.read():
            print("[ALREADY_SENT]")
            sys.exit(0)
with open(log_path, "a") as f:
    f.write(log_content + "\n")

account_id = "o9cq804Yq-r837AH5C_ou5qzp_kg@im.wechat"
token = "5221a5d8d221@im.bot:060000d32c32e556453f4d78562bed9db7094c"
chat_id = "o9cq804Yq-r837AH5C_ou5qzp_kg@im.wechat"

async def send():
    await wx.send_weixin_direct(extra={"account_id": account_id}, token=token, chat_id=chat_id, message=msg)

asyncio.run(send())
print("[30MIN_SENT]")
```

---

## 关键发现（踩坑记录）

1. **不要用 `WechatMessageAPI`** — `gateway.platforms.weixin` 模块没有这个类，会报 `AttributeError`。
2. **正确 API 是 `send_weixin_direct`** — 这是 one-shot 发送辅助函数，绕过 adapter 生命周期。
3. **`extra={"account_id": account_id}` 必须传** — 仅传 `token` 会报 `Weixin account ID missing` 错误。`account_id` 就是 `user_id` 字段的值（完整格式 `o9cq804Yq-r837AH5C_ou5qzp_kg@im.wechat`）。
4. **token 从 `@im.bot.json` 文件读取** — 格式 `xxxxx@im.bot:xxxxxxxxx`。
5. **发送前写日志** — 防止 cron 重复运行时重复发送。
6. **`ast.literal_eval` 解析** — `meetings_latest.txt` 存的是 Python 字面量元组数组，不能用 `json.loads`。
7. **每周日触发一次总览** — cron 表达式 `0 18 * * 0`（每周日18点），用于收到PDF后输出
8. **会议前30分钟提醒** — cron 表达式 `*/5 * * * *`（每5分钟检查一次），避免精确时间点cron丢失

## 日志文件

- 7点发送日志：`/home/dministrator/.hermes/data/daily_7am_reminder_log.txt`
- 30分钟提醒日志：`/home/dministrator/.hermes/data/meeting_30min_log.txt`

## 验证步骤
```bash
python -c "import gateway.platforms.weixin as wx; print(dir(wx))" | grep -i send
# 确认有 send_weixin_direct
```

## 验证步骤
```bash
python -c "import gateway.platforms.weixin as wx; print(dir(wx))" | grep -i send
# 确认有 send_weixin_direct
```
