---
name: playwright-wsl-chromium-launch
description: 在 WSL (Ubuntu) 中启动 Playwright Chromium 的故障排除——解决 libnspr4.so 等系统库缺失问题
triggers:
  - chromium 无法启动 "error while loading shared libraries"
  - playwright 浏览器在 WSL 中报错
  - libnspr4.so: cannot open shared object file
---

# Playwright Chromium 在 WSL 中启动失败

## 典型错误
```
error while loading shared libraries: libnspr4.so: cannot open shared object file
```

## 排查路径

### 1. 安装系统依赖（需要 sudo）
```bash
npx playwright install-deps chromium
# 或手动：
sudo apt-get install -y libnspr4 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1
```

### 2. 使用 Windows Chrome（不需要 Linux 库）
WSL 可以直接调用 Windows 的 Chrome/Edge：
```bash
# 查找 Windows Chrome 路径（PowerShell）
powershell.exe -Command "Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe' | Select-Object -ExpandProperty '(default)'"

# playwright 配置中指定 executablePath：
# "executablePath": "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
```

### 3. 验证浏览器是否可用
```bash
node -e "
const { chromium } = require('playwright-core');
(async () => {
  const browser = await chromium.launch({ 
    executablePath: '/mnt/c/Program Files/Google/Chrome/Application/chrome.exe',
    args: ['--no-sandbox']
  });
  const page = await browser.newPage();
  await page.goto('https://www.baidu.com');
  console.log(await page.title());
  await browser.close();
})();
"
```

## playwright-cli 相关路径（已验证）
- CLI 路径：`/mnt/e/her/playwright-cli-main/`
- 浏览器缓存：`~/.cache/ms-playwright/chromium_headless_shell-1219/`
- 配置：`/mnt/e/her/playwright-cli-main/.playwright/cli.config.json`

## 已知障碍
- WSL 无 root 权限时，apt-get install 依赖会静默失败（exit 0 但库未安装）
- Windows Chrome 在 WSL 中的标准路径：`/mnt/c/Program Files/Google/Chrome/Application/chrome.exe`
- find /mnt/c -name "chrome.exe" 搜索超时，不要用完整扫描

## 关键发现（本 session）

### 非交互式 sudo 技巧（无 TTY 环境下）
如果 sudo 需要密码但无 TTY 输入，用 `echo password | sudo -S`：
```bash
echo 'sunjian123' | sudo -S apt-get install -y libnspr4 libnss3 libatk1.0-0 ...
```
**注意**：密码会以明文出现在命令历史中，生产环境慎用。

### playwright-cli 标准工作流（已验证）
playwright-cli 需要先启动持久浏览器，再通过 session 执行命令：
```bash
# 1. 启动浏览器（后台运行）
node playwright-cli.js open

# 2. 后续命令加 -s=default
node playwright-cli.js -s=default goto "https://cn.bing.com/search?q=孙剑"
node playwright-cli.js -s=default screenshot

# 3. 关闭浏览器
node playwright-cli.js -s=default close
```

### 网络限制
- **百度**：从此 WSL 环境访问超时（可能被墙），无法加载
- **Bing**：正常工作，cn.bing.com 可用
- 搜"孙剑"结果主要是旷视科技首席科学家孙剑（已故）
