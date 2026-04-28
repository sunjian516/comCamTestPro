---
name: xiaohongshu-scraping
description: 小红书（Xiaohongshu/RED）网页内容抓取——探索页可匿名访问，搜索结果需登录
---

# 小红书（XHS）抓取

## 关键发现

| 页面 | 登录要求 | 可行性 |
|------|----------|--------|
| 探索首页 `xiaohongshu.com/explore` | ❌ 不需要 | ✅ 可抓 |
| 搜索结果页 `search_result?keyword=xxx` | ✅ 需要 | ❌ 强制跳转登录 |
| 笔记详情页 `explore/xxx` | ✅ 需要 | ❌ 强制跳转登录 |
| API 接口 | ✅ 需要 | ❌ 认证失败 |

**核心问题**：搜索功能必须登录，playwright stealth 无法绕过。

---

## 可行的抓取方案

### 方案：探索页（首页推荐）

```javascript
const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

(async () => {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    
    // 注意：用 'commit' 而不是 'networkidle'——XHS 长连接会导致 networkidle 超时
    await page.goto('https://www.xiaohongshu.com/explore', {
        waitUntil: 'commit',
        timeout: 15000
    });
    
    // 等待内容加载
    await page.waitForTimeout(5000);
    
    const bodyText = await page.evaluate(() => document.body.innerText);
    console.log(bodyText.substring(0, 3000));
    
    await browser.close();
})();
```

---

## 方案A：登录 cookies（推荐用于搜索）

1. 用户在浏览器登录小红书
2. 导出 cookies（浏览器开发者工具 → Application → Cookies）
3. agent 存储 cookies
4. 定时任务用 cookies + playwright 访问搜索页

**缺点**：cookies 有时效性，需要定期更新

---

## 方案B：换平台

| 平台 | 搜索无需登录 | 替代性 |
|------|-------------|--------|
| 微信公众号 | ❌ 需要 | — |
| 微博 | ✅ 不需要 | ⭐ 推荐 |
| 知乎 | ✅ 可绕过 | ⭐ 已有技能 |
| 百度 | ✅ 不需要 | 可用 |

---

## 已知限制

- `waitUntil: 'networkidle'` 会超时，改用 `'commit'`
- 页面有防爬检测，频繁访问可能触发验证码
- 探索页内容是"推荐算法"随机feed，无法精准搜索关键词
- 纯文字内容在 innerText 中，图片/视频内容需额外处理

---

## 状态

**当前**：探索页可抓，搜索不可用。需要用户考虑是用 cookies 方案还是换微博监控负面新闻。
