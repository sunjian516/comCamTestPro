---
name: bypass-bot-detection
description: 使用 playwright-extra + puppeteer-extra-plugin-stealth 绕过网站机器人检测
version: 1.0.0
author: Hermes Agent
tags: [playwright, stealth, anti-bot, web-scraping, nodejs]
---

# 绕过网站机器人检测

## 问题

使用标准 Playwright 或 curl 访问某些网站时被检测为机器人，返回 403 或拒绝访问。

**典型网站**：CSDN、知乎、某些需要登录的内容站

## 解决方案

使用 Node.js 版本的 `playwright-extra` + `puppeteer-extra-plugin-stealth`，**而非 Python 版本**。

### Python 版本的问题

```python
# ❌ playwright_stealth (Python) 有 API 问题
from playwright_stealth import stealth  # 这是一个 module，不是可调用函数
from playwright_stealth import Stealth  # Stealth().apply_stealth_sync() 但仍被检测

# ❌ 尝试的各种方式都失败
chromium.use(stealth())  # TypeError
```

### 正确的 Node.js 方式

```bash
# 在项目目录安装依赖（需要 npm）
cd /path/to/playwright-cli-main
npm install playwright-extra puppeteer-extra-plugin-stealth
```

```javascript
const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  // 使用 domcontentloaded 而非 load，更快完成
  await page.goto('https://example.com', { 
    timeout: 60000,
    waitUntil: 'domcontentloaded'
  });
  
  // 等待内容加载
  await page.waitForTimeout(8000);
  
  // 获取 HTML 内容
  const content = await page.content();
  
  // 保存截图
  await page.screenshot({ path: '/tmp/screenshot.png' });
  
  await browser.close();
})();
```

## 关键要点

1. **使用 Node.js 而非 Python**：`playwright-extra` + `puppeteer-extra-plugin-stealth` 组合在 Node 下更可靠

2. **waitUntil 用 `domcontentloaded`**：不要用 `load`（默认），后者会等待所有资源（包括图片字体），容易超时

3. **额外等待时间**：`waitForTimeout(5000-8000)` 给 JS 渲染留出时间

4. **超时设置**：给 `goto` 设置 60-120 秒超时

5. **知乎特别难**：即使这样处理，知乎（zhihu.com）仍然超时无法访问，可能需要特殊网络环境

## 已验证可绕过检测的网站

- ✅ CSDN (blog.csdn.net)

## 无法绕过的网站

- ❌ 知乎 (zhuanlan.zhihu.com) - 超时
- ❌ Google - 在 WSL 环境中网络限制

## playwright-cli 项目位置

```
/mnt/e/her/playwright-cli-main
```

该目录已配置好 npm 环境，可直接使用。
