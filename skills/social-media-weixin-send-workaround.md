---
name: weixin-send-workaround
description: Send WeChat/Weixin messages and files reliably — key insight: use terminal() instead of execute_code() so environment variables are loaded.
version: 2.0.0
author: hermes-agent
license: MIT
platforms: [linux, wsl]
prerequisites:
  - WeChat/Weixin account configured in Hermes (accounts stored in ~/.hermes/weixin/)
  - Valid Weixin target ID (e.g. o9cq804Yq-r837AH5C_ou5qzp_kg@im.wechat)
metadata:
  hermes:
    tags: [weixin, wechat, send_message, terminal, execute_code, file-send, cron]
---

# WeChat (Weixin) Send Workaround

## The Core Principle: terminal() vs execute_code()

**微信发送必须用 `terminal()`，不能用 `execute_code()`！**

- `execute_code` 的 Python 沙盒**不加载环境变量**，WEIXIN_TOKEN 等为空
- 症状错误：`{"error": "Platform 'weixin' is not configured..."}` — 这个错不是说微信没配置，而是 token 读不到
- `terminal()` 运行在完整 shell 环境，变量正常加载，发送成功

## Send via terminal()

```python
terminal(command="""cd /home/dministrator/projects/hermes-agent && source venv/bin/activate && python3 -c "
import sys; sys.path.insert(0, '.')
from tools.send_message_tool import send_message_tool
result = send_message_tool({
    'action': 'send',
    'target': 'weixin:o9cq804Yq-r837AH5C_ou5qzp_kg@im.wechat',
    'message': '测试消息',
    'media_files': [('/mnt/e/her/workspace/02 知识库/运保合同全生命周期管理表.xlsx', False)],
})
print(result)
" """)
```

成功返回：`{"success": true, "platform": "weixin", "message_id": "hermes-weixin-..."}`

## send_message tool (直接调用)

通过 send_message 工具本身发送时，工具运行在正确环境里，不需要额外处理：
```
target: weixin:o9cq804Yq-r837AH5C_ou5qzp_kg@im.wechat
message: 请查收
media_files: /mnt/c/Users/Administrator/Desktop/文件.xlsx
```

## Images / Files — Verified Working

- 图片（JPEG/PNG/GIF）→ send_document via CDN upload，✅ 成功
- 文件（Excel/PDF/ZIP）→ send_document via CDN upload，✅ 成功
- AES-128-ECB 加密上传，~1.7ms/文件
- 11777 字节 Excel 测试通过

之前"图片/文件发送失败"的结论是误判，真实原因是环境变量未加载导致根本没走到 API。

## Windows Desktop 备用方案

如 API 发送失败，复制到 Windows 桌面：
```bash
cp /path/to/file.xlsx /mnt/c/Users/Administrator/Desktop/file.xlsx
```

桌面路径：`/mnt/c/Users/Administrator/Desktop/`

## 根因

微信 iLink 适配器使用 asyncio 进行 CDN 上传（AES-128-ECB 加密 + CDN POST）。从 execute_code 沙盒调用时：环境变量未加载 → token 为空 → 直接报"未配置"。terminal() 有完整 shell 环境 → token 正常 → CDN 上传成功。

## delegate_task（已不需要）

之前用 delegate_task 规避"Timeout context manager"错误，但真正的修复是使用 terminal() 让环境变量正确加载。

## 目标用户 ID（只读参考）

- 目标：o9cq804Yq-r837AH5C_ou5qzp_kg@im.wechat
- Home channel：o9cq804Yq-r837AH5C_ou5qzp_kg@im.wechat

---

## ⚠️ CDN Session 超时（errcode=-14）—— 文件发送失败

**症状：** `send_message` 返回 `success: true`，但对方没收到文件。日志显示：
```
iLink sendmessage error: ret=-2 errcode=-14 errmsg=session timeout
```

**原因：** iLink CDN 上传 session 过期（通常1-2周），文本消息走长连接正常，文件/图片/视频上传需要 CDN session。

**解法：** 重新扫码刷新登录状态。

### 步骤 1/2 — 生成新二维码

```bash
cd /home/dministrator/projects/hermes-agent && source venv/bin/activate && python3 << 'EOF'
import asyncio, aiohttp, os, qrcode, json

async def get_qr():
    token = os.environ['WEIXIN_TOKEN']
    base_url = 'https://ilinkai.weixin.qq.com'
    async with aiohttp.ClientSession(trust_env=True) as session:
        resp = await session.get(
            f'{base_url}/ilink/bot/get_bot_qrcode?bot_type=3',
            headers={'token': token},
            timeout=aiohttp.ClientTimeout(total=30)
        )
        data = await resp.json()
        qr_url = data.get('qrcode_img_content') or data.get('qrcode')
        if qr_url:
            # 生成二维码图片
            qr = qrcode.QRCode(version=1, box_size=10, border=2)
            qr.add_data(qr_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color='black', back_color='white')
            img.save('/tmp/weixin_refresh_qr.png')
            print('QR saved to /tmp/weixin_refresh_qr.png')
            print('URL:', qr_url)

asyncio.run(get_qr())
EOF
```

### 步骤 2/2 — 发送二维码给用户扫码

```python
terminal(command="""cd /home/dministrator/projects/hermes-agent && source venv/bin/activate && python3 -c "
import sys; sys.path.insert(0, '.')
from tools.send_message_tool import send_message_tool
result = send_message_tool({
    'action': 'send',
    'target': 'weixin:o9cq804Yq-r837AH5C_ou5qzp_kg@im.wechat',
    'message': '请用微信扫描此二维码来刷新登录状态（用于文件传输），扫码后请在手机上确认',
    'media_files': [('/tmp/weixin_refresh_qr.png', False)],
})
print(result)
"
""")
```

用户扫码确认后，文件发送自动恢复正常。

### 验证修复

```python
terminal(command="""cd /home/dministrator/projects/hermes-agent && source venv/bin/activate && python3 -c "
import sys; sys.path.insert(0, '.')
from tools.send_message_tool import send_message_tool
result = send_message_tool({
    'action': 'send',
    'target': 'weixin:o9cq804Yq-r837AH5C_ou5qzp_kg@im.wechat',
    'message': '测试',
    'media_files': [('/mnt/e/her/workspace/02 知识库/运保合同全生命周期管理表.xlsx', False)],
})
print(result)
"
""")
```

成功返回：`{"success": true, "platform": "weixin", "message_id": "hermes-weixin-..."}`

---

## 排查路径（快速定位）

| 症状 | 原因 | 解法 |
|------|------|------|
| `error: Platform 'weixin' is not configured` | `execute_code` 沙盒没有加载 .env | 改用 `terminal()` |
| `errcode=-14: session timeout` | CDN session 过期 | 重新扫码（见上文） |
| `error: Timeout context manager...` | 在错误上下文调用异步代码 | 用 `terminal()` |
| 文件路径含 `\n` 或特殊字符 | 路径格式错误 | 用绝对路径，不含引号转义 |
| 文本发成功，文件收不到 | CDN session 过期 | 重新扫码 |
