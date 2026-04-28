---
name: playwright-browser-setup
description: Playwright CLI browser setup on WSL/Linux - system deps, Chinese fonts, WeChat media sending
---
# Playwright Browser Setup (WSL/Linux)

## Problem
Playwright Chromium fails to launch on fresh Linux/WSL with:
`error while loading shared libraries: libnspr4.so: cannot open shared object file`

## Solution
Install Chromium system dependencies:
```bash
echo 'PASSWORD' | sudo -S apt-get install -y \
  libnspr4 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
  libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
  libxrandr2 libgbm1 libpango-1.0-0 libcairo2
```

## Chinese Font (for screenshots)
If Chinese characters render as blank/garbled in screenshots:
```bash
echo 'PASSWORD' | sudo -S apt-get install -y fonts-noto-cjk
echo 'PASSWORD' | sudo -S fc-cache -f
```

## Playwright-Cli Usage
```bash
cd /path/to/playwright-cli-main
node playwright-cli.js open                           # open browser
node playwright-cli.js -s=default goto "URL"          # navigate
node playwright-cli.js -s=default screenshot           # screenshot
node playwright-cli.js -s=default close                 # close
```

## 绕过反爬检测（针对中国网站 CSDN/知乎等）

**推荐方案**：使用 `playwright-extra` + `puppeteer-extra-plugin-stealth`（Node.js 版本）

### 安装
```bash
cd /mnt/e/her/playwright-cli-main
npm install playwright-extra puppeteer-extra-plugin-stealth
```

### 使用示例
```javascript
const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('https://blog.csdn.net/example/article/123', { 
    timeout: 60000,
    waitUntil: 'domcontentloaded'  // 关键：用 domcontentloaded 而非 load
  });
  
  await page.waitForTimeout(8000);  // 中国网站需要更长渲染时间
  
  const content = await page.content();
  require('fs').writeFileSync('/tmp/article.html', content);
  
  await browser.close();
})();
```

### 注意事项
- **必须用 Node.js 版本**，Python playwright-stealth 无效
- 使用 `domcontentloaded` 而非默认 `load`，更快且更少被检测
- 等待时间要够长（5-8秒）让 JS 完成渲染
- 知乎即使 stealth 插件也可能无法访问（需要特殊网络环境）

### Windows 代理方案
如需通过 Windows IP 出口，在 Windows 运行代理后：
```javascript
browser = await chromium.launch({
  proxy: { server: 'http://<Windows_IP>:<端口>' }
});
```
常见端口：7890、1080、8080、10808

## Screenshot Timeout Issue
fonts-noto-cjk is large (200MB+) and causes `waiting for fonts to load...` timeout during screenshot. Wait 3-5s after page load before taking screenshot.

## 已知限制：Windows浏览器在WSL中无法headless运行
Windows Edge/Chrome路径（如 `/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe`）在WSL中无法以headless模式启动Playwright，会报错：
```
Remote debugging pipe file descriptors are not open.
Target page, context or browser has been closed
```
**解决方案**：使用WSL本地安装的Chromium（需要apt-get安装依赖），或使用Bing搜索API获取网页内容摘要。

## 难抓取网站列表
以下网站有强反爬/JS渲染机制，curl/urllib直接请求会被拦截：
- 知乎 (zhihu.com) - 需要JS渲染
- CSDN (csdn.net) - 403 Forbidden
- 微信公众号文章 - 需要JS渲染

**替代方案**：使用Bing搜索API获取摘要，或让用户提供文章内容。

## WeChat Media Sending
send_message with MEDIA: fails from foreground context with "Timeout context manager should be inside a task". Use delegate_task to send images:
```
delegate_task(goal="Send image /path/to/img.png to WeChat user ID with message 'text'", toolsets=['web'])
```
Alternative: copy to Windows desktop (`/mnt/c/Users/.../Desktop/`) and notify user to open manually.
