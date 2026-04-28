---
name: wsl2-usb-camera-passthrough
description: WSL2 访问 Windows USB摄像头的方案与限制
version: 1.0.0
author: hermes-agent
tags: [wsl2, usb, camera, windows]
---

# WSL2 USB摄像头穿透

## 结论

**WSL2 默认无法直接访问插在 Windows 上的 USB 摄像头**。`/dev/video*` 设备在 WSL 里不存在。

## 已验证的硬限制

1. WSL2 和 Windows 的 USB 总线是隔离的
2. WSL 里无法运行 Windows 的 .exe/.msi 安装包（binary format incompatible）
3. WSL 里无法通过 `\\wsl$` 互操作运行 Windows 程序（Exec format error）
4. GitHub 在当前网络环境不可访问（`curl github.com` — Connection refused）

## 可行的解决方案

### 方案1：usbipd-win（需要 Windows 11+）
- 在 Windows 上安装 [usbipd-win](https://github.com/dorssel/usbipd-win/releases)
- **注意**：Windows 10 不支持 USBIP，需要 Windows 11 或 Windows Server 2022+
- 适用版本确认：`wsl.exe --status` 或 `usbipd --version`

### 方案2：Python + OpenCV + 网络传输
- 在 Windows 上运行 Python（OpenCV）读取摄像头
- 通过 HTTP/UDP 把视频流传送到 WSL
- 示例：Windows 端 `python -m http.server`，WSL 端用 ffmpeg 拉流

### 方案3：Windows 侧中转
- 在 Windows 上运行 OBS Virtual Camera 或类似工具
- WSL 通过 V4L2Loopback 接收（需要内核模块，WSL2 不支持）

## 当前环境网络状态
- ✅ 可访问：百度、淘宝
- ❌ 不可访问：Google、GitHub、YouTube
- DNS 可用，但 TCP 连接被阻断
