---
name: bypass-cn-site-detection
description: 绕过中国网站（CSDN、知乎等）的反爬检测，成功抓取内容
version: 1.0.0
author: Hermes Agent
license: MIT
tags: [playwright, stealth, anti-bot, crawler, china]
---

# 绕过中国网站反爬检测

## 问题
CSDN、知乎等中国网站有严格的反自动化检测：
- 检测 `navigator.webdriver` 标志
- Headless 模式特征识别
- 浏览器指纹不完整
- TLS 握手异常

普通 Playwright 或 curl 直接访问会返回 403 或超时。

## 解决方案：playwright-extra + puppeteer-extra-plugin-stealth

**必须使用 Node.js 版本**，Python 版本无效。

### 1. 安装依赖
```bash
cd /path/to/your/project
npm install playwright-extra puppeteer-extra-plugin-stealth
```

### 2. 使用示例
```javascript
const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  // 关键：使用 domcontentloaded 而非默认的 load
  await page.goto('https://example.com', { 
    timeout: 60000,
    waitUntil: 'domcontentloaded'
  });
  
  // 等待内容加载
  await page.waitForTimeout(8000);
  
  const title = await page.title();
  const content = await page.content();
  
  console.log('Title:', title);
  console.log('Content length:', content.length);
  
  await browser.close();
})().catch(e => console.error('Error:', e.message));
```

### 3. 关键配置参数

#### waitUntil 选择（重要！）
```javascript
// ✅ 推荐 for 中国网站 - 等待网络空闲
await page.goto(url, { 
  timeout: 300000,  // 知乎需要5分钟超时
  waitUntil: 'networkidle'  // 等待所有网络请求完成
});

// ✅ 备选 - 更快
waitUntil: 'domcontentloaded'
```

#### Context 配置（提升成功率）
```javascript
const context = await browser.newContext({
  viewport: { width: 1920, height: 1080 },
  user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  locale: 'zh-CN',
  timezone_id: 'Asia/Shanghai'
});
const page = await context.newPage();
```

#### 等待时间要够长
```javascript
await page.waitForTimeout(15000); // 中国网站需要更长的 JS 渲染时间
```

#### 截图可能超时
```javascript
// 如果页面有大量字体资源，截图会等待字体加载导致超时
// 可以先保存 HTML 内容
require('fs').writeFileSync('/tmp/page.html', content);
```

## 验证方法

成功标志：
- `page.title()` 返回正常标题（不是 "403 Forbidden"）
- `content.length` > 10000 bytes
- 知乎、知乎等页面正常加载

失败标志：
- `TimeoutError` - 大概率被检测，需要增加等待时间
- `403 Forbidden` - IP 或行为被拒绝
- 内容长度 < 1000 bytes - 可能返回的是错误页面

## 测试通过的网站

| 网站 | 状态 | 备注 |
|------|------|------|
| CSDN | ✅ | 直接可用 |
| 知乎 | ✅ | 需要 `networkidle` + 长超时 |
| - | - | - |

## 代理方案

如果需要通过 Windows IP 出口访问，在 Windows 上运行代理（如 Clash、v2ray 等），然后：

```javascript
const browser = await chromium.launch({
  proxy: {
    server: 'http://<Windows_IP>:<代理端口>'
  }
});
```

常见代理端口：7890、1080、8080、10808
