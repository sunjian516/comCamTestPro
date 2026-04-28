---
name: web-search-cn
description: 在中国环境（Linux/WSL）中搜索百度和必应——百度需要浏览器，必应可直接 urllib 抓取。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [search, baidu, bing, china, web]
---

# Web Search in China (百度/必应)

## 背景
在中国环境的 Linux/WSL 中，直接用 curl/urllib 访问百度会被安全验证拦截，需要浏览器。必应（Bing）则没有这个问题。

## 百度搜索
百度有严格反爬，curl/urllib 请求会被跳转到安全验证页面。需要 Playwright 浏览器自动化：

```python
# 方式1: Python playwright (需要系统依赖 libnspr4 等)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
    page = browser.new_page()
    page.goto('https://www.baidu.com')
    page.fill('#kw', '搜索词')
    page.click('input[type="submit"]')
    # ... 提取结果
```

**系统依赖问题**: 如果报 `libnspr4.so: cannot open shared object file`，需要 `apt-get install libnspr4 libnss3 ...`，但可能没有 root 权限。

**WSL 中的 Windows 浏览器**: 可以尝试指向 Windows 上的 Chrome/Edge：
```javascript
const { chromium } = require('playwright-core');
const browser = await chromium.launch({
    executablePath: '/mnt/c/Program Files/Google/Chrome/Application/chrome.exe',
    // 或 Edge: '/mnt/c/Program Files/Microsoft/Edge/Application/msedge.exe'
});
```

## 必应（Bing）搜索 ✅ 推荐
必应对自动化请求友好，可用 urllib 直接抓取：

```python
import urllib.request
import urllib.parse
import re

url = "https://cn.bing.com/search?q=" + urllib.parse.quote("搜索词")
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
})
with urllib.request.urlopen(req, timeout=15) as r:
    content = r.read().decode('utf-8', errors='ignore')

# 提取搜索结果
results_section = re.search(r'<ol[^>]*id="b_results"[^>]*>(.*?)</ol>', content, re.DOTALL)
cards = re.findall(r'<li[^>]*class="[^"]*b_algo[^"]*"[^>]*>(.*?)</li>', results_section.group(1), re.DOTALL)
for card in cards[:10]:
    title = re.search(r'<h2[^>]*>(.*?)</h2>', card, re.DOTALL)
    link = re.search(r'href="(https?://[^"?]+)"', card)
    snippet = re.search(r'<p[^>]*>(.*?)</p>', card, re.DOTALL)
    # 打印结果...
```

## Playwright 安装（Node.js 版本）
npm 安装的 playwright-core 能找到系统浏览器，但 pip 安装的 Python 版本可能路径不一致：
```bash
# Node.js 版本（npm）
cd /home/dministrator/.npm/_npx/.../node_modules/playwright-core
npx playwright install chromium

# Python 版本
/usr/bin/python3 -m playwright install chromium
```
