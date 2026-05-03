---
name: wsl2-usb-camera-passthrough
description: WSL2 USB摄像头穿透方案与替代方案。记录了usbipd穿透对某些UVC设备的已知限制（uvcvideo初始化失败-5），以及通过IP摄像头软件+RTSP流替代USB passthrough的完整流程。
version: 2.0.0
author: hermes-agent
tags: [wsl2, usb, camera, windows, rtsp]
state: proven
---

# WSL2 USB摄像头访问

## 结论

**usbipd passthrough 可行但有设备兼容性限制**，部分UVC设备会初始化失败。最终方案推荐IP摄像头软件+RTSP流。

## 已验证的两种路径

### 路径A：usbipd-win USB passthrough（部分设备可用）

```powershell
# Windows 管理员终端
usbipd list                                    # 找到摄像头busid
usbipd attach --wsl --busid <busid>           # 穿透到WSL
```

**问题**：某些UVC 1.00设备在WSL中`dmesg`能检测到，但`/dev/video*`节点不创建，初始化返回`-5`：
```
uvcvideo 1-1:1.1: Failed to initialize the device (-5)
```
已验证失败的设备：Hamedal C10 (0525:a4b0) — UVC协议不完全兼容

**判断方法**：
```bash
dmesg | grep -i "uvc"        # 设备是否被检测
ls /dev/video*              # 节点是否存在（关键判断）
```

### 路径B：IP摄像头软件 + RTSP（通用可靠）

在Windows端装IP摄像头软件，把摄像头发成RTSP流，WSL通过RTSP读取，完全绕过USB passthrough。

**步骤1**：Windows端安装 [IP Camera](https://apps.microsoft.com/store/detail/ip-camera/9nblggh3ns7c)（Windows Store，免费），启动后默认发流：`rtsp://127.0.0.1:8554/live`

**步骤2**：WSL端读取RTSP流
```python
import cv2
rtsp_url = "rtsp://127.0.0.1:8554/live"
cap = cv2.VideoCapture(rtsp_url)
ret, frame = cap.read()
if ret:
    cv2.imwrite('/tmp/capture.jpg', frame)
cap.release()
```

**注意**：RTSP流需要Windows防火墙放行8554端口。
