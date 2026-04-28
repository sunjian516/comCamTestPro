---
name: weixin-file-send
description: Send files and messages to WeChat via Hermes gateway's WeixinAdapter. Uses send_weixin_direct directly, discovers bot credentials from account JSON files, handles session timeout errors.
version: 1.0.0
author: hermes-agent
license: MIT
metadata:
  hermes:
    tags: [wechat, weixin, messaging, file-send, social-media]
    platform: weixin
prerequisites:
  python_paths: [gateway.platforms.weixin]
---

# WeChat File Sending via Hermes Gateway

Send files and text messages to WeChat users through Hermes using `send_weixin_direct`.

## Finding Bot Credentials

WeChat bot credentials live in `~/.hermes/weixin/accounts/*.json` (NOT in config.yaml — those entries are empty).

```python
import os, json

accounts_dir = "/home/dministrator/.hermes/weixin/accounts"
bot_creds = []
for f in os.listdir(accounts_dir):
    if f.endswith("@im.bot.json"):
        path = os.path.join(accounts_dir, f)
        with open(path) as fp:
            data = json.load(fp)
        bot_creds.append({
            "account_id": data.get('user_id', '').split('@')[0],  # e.g. "3dc83b5df867@im.bot"
            "token": data.get('token', ''),                         # full token string
            "wechat_user_id": data.get('user_id', '')               # bot's own WeChat ID
        })
```

Multiple bot accounts may exist — try each if one fails with session timeout.

## Sending a File with Message

```python
import sys, os, asyncio
sys.path.insert(0, '/home/dministrator/projects/hermes-agent')
os.chdir('/home/dministrator/projects/hermes-agent')
import gateway.platforms.weixin as wx

async def send_file(chat_id: str, file_path: str, message: str = ""):
    # Use first bot account — try others if this fails
    creds = bot_creds[0]  # or iterate through all
    return await wx.send_weixin_direct(
        token=creds["token"],
        extra={"account_id": creds["account_id"]},
        chat_id=chat_id,
        message=message,
        media_files=[(file_path, False)]  # (path, is_voice)
    )

user_id = "o9cq804Yq-r837AH5C_ou5qzp_kg@im.wechat"
asyncio.run(send_file(user_id, "/path/to/file.html", "请查收文件"))
```

## Sending Files (Critical: Use execute_code)

**NEVER use `send_message` tool directly for file sending** — it will fail with `"Timeout context manager should be used inside a task"`.

Always use `execute_code` with `asyncio.run()` + `send_weixin_direct`:

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

async def send_file(chat_id: str, file_path: str, message: str = ""):
    for creds in bot_creds:
        try:
            return await wx.send_weixin_direct(
                token=creds["token"],
                extra={"account_id": creds["account_id"]},
                chat_id=chat_id,
                message=message,
                media_files=[(file_path, False)]  # (path, is_voice)
            )
        except Exception as e:
            print(f"Failed: {e}")
    return None

user_id = "o9cq804Yq-r837AH5C_ou5qzp_kg@im.wechat"  # 老板
asyncio.run(send_file(user_id, "/tmp/screenshot.png", "截图"))
```

## Known Failure Modes

### All bots fail simultaneously
When all 3 bot accounts return errors:
- Bot1 (5221a5d8d221): `ret=-2 errcode=None errmsg=unknown error`
- Bot2 (3dc83b5df867): `ret=-14 errmsg=session timeout`
- Bot3 (9476b24f7fb8): `ret=-14 errmsg=session timeout`

This indicates the Hermes WeChat gateway itself is disconnected from the iLink service. Try:
1. Restart the hermes-gateway process: `kill <pid>` and let cron respawn it, or find the restart command
2. If that doesn't work, the gateway has been running continuously since Apr24 (pid 1009) — long-running process may have connection leaks; a full restart may be needed

### Individual bot session timeout
- Error: `iLink sendmessage error: ret=-14 errmsg=session timeout`
- Fix: Try another bot account; if all timeout, fall back to above gateway restart

### Bot returns unknown error (ret=-2)
- Error: `iLink sendmessage error: ret=-2 errcode=None errmsg=unknown error`
- This bot account may be blocked or the gateway connection is degraded. Try other bots.

## Common Errors

| Error message | Cause | Fix |
|--------------|-------|-----|
| `"Weixin token missing"` | Token not provided or empty string | Ensure `token=` is passed from bot JSON |
| `"Weixin account ID missing"` | `account_id` missing from extra | Include `extra={"account_id": "..."}` |
| `"iLink sendmessage error: ... session timeout"` | Bot session expired | Try another bot account; may need gateway restart |
| `"Timeout context manager should be used inside a task"` | Using `send_message` tool directly for files | Use `execute_code` with `asyncio.run()` + `send_weixin_direct` instead |
| `"iLink sendmessage error: ret=-2"` | Bot/account degraded | Try other bot accounts; if all fail, restart gateway |

## Critical Rules

1. **Always use `execute_code` with `asyncio.run()`** — never call `send_message` tool directly for WeChat file sends
2. **`send_weixin_file` does not exist** — the correct function is `send_weixin_direct`
3. **Config.yaml WeChat entries are empty** — read credentials from the `~/.hermes/weixin/accounts/` JSON files
4. **`_LIVE_ADAPTERS` dict is empty** in import context — `send_weixin_direct` handles this by creating a sessionless adapter per call
5. **Session timeout errors** may require trying multiple bot accounts or restarting the gateway

## Known WeChat IDs

- User: `o9cq804Yq-r837AH5C_ou5qzp_kg@im.wechat`
