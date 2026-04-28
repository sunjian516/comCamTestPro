---
name: web-scraping-stealth
description: 使用playwright-extra + puppeteer-extra-plugin-stealth绕过反爬抓取知乎/CSDN等网站
tags: [playwright, stealth, scraper, 知乎, 反爬]
---

# Web Scraping with Stealth - 绕过反爬抓取网页

## Problem
普通 requests/urllib/Python playwright 会被知乎、CSDN 等网站检测并拦截。

## Solution

### 环境准备

```bash
mkdir -p /mnt/e/her/playwright-cli-main
cd /mnt/e/her/playwright-cli-main
npm init -y
npm install playwright-extra puppeteer-extra-plugin-stealth
npx playwright install chromium
```

### 核心抓取脚本 (scrape.js)

```javascript
const { chromium } = require('playwright-extra');
const stealthPlugin = require('puppeteer-extra-plugin-stealth')();
const fs = require('fs');

chromium.use(stealthPlugin);

const url = process.argv[2];
const outputPath = process.argv[3] || '/tmp/page.html';

if (!url) {
    console.log('Usage: node scrape.js <url> [output_path]');
    process.exit(1);
}

(async () => {
    const browser = await chromium.launch({ 
        headless: true,
        args: ['--disable-blink-features=AutomationControlled', '--no-sandbox']
    });
    
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1920, height: 1080 });
    
    try {
        await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });
        await page.waitForTimeout(2000);
        
        const content = await page.content();
        fs.writeFileSync(outputPath, content);
        console.log(`Success! Saved ${content.length} bytes to ${outputPath}`);
    } catch (err) {
        console.error(`Error: ${err.message}`);
    } finally {
        await browser.close();
    }
})();
```

### 使用方法

```bash
cd /mnt/e/her/playwright-cli-main
node scrape.js "https://zhuanlan.zhihu.com/xxx" /tmp/zhihu.html
```

---

## 知乎内容提取

知乎内容存储在 `window.__INITIAL_STATE__` JSON中，用正则提取：

```python
import re, json

def extract_zhihu_content(html_path, output_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    match = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.+?\});', html, re.DOTALL)
    if match:
        json_str = match.group(1).replace('undefined', 'null')
        data = json.loads(json_str)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
        print(f"Extracted to {output_path}")

# 使用
python extract_zhihu.py /tmp/zhihu.html /tmp/zhihu_content.txt
```

---

## Pitfalls

1. **仍然是自动化检测** → 降低请求频率或用住宅代理
2. **懒加载内容** → 加 `page.evaluate()` 滚动触发
3. **知乎需要登录** → 用 `page.context().addCookies()` 注入 cookies
4. **内容乱码** → 检查页面编码设置

## Verification

```bash
ls -lh /tmp/page.html
head -c 500 /tmp/page.html
grep -o "关键词" /tmp/page.html | head -3
```

## Related Skills

- `playwright-browser-setup` - 浏览器安装排障
- `bypass-cn-site-detection` - 中国网站反爬备用方案
