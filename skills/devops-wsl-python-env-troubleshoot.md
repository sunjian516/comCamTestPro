---
name: wsl-python-env-troubleshoot
description: WSL 环境 Python 多版本共存时的包安装与导入排障——重点解决 hermes-agent venv 缺 pip、系统 Python 与 venv Python 混用导致 numpy import 失败的问题。
---

# WSL Python 环境排障与依赖安装

## 典型症状

运行 Python 时报 `ModuleNotFoundError` 或 `ImportError: numpy C-extensions failed`，且涉及多个 Python 版本共存环境。

## 排查流程

### 1. 确认 Python 解释器路径
```bash
which python3          # 当前 shell 的 python
python3 --version      # 版本
# hermes-agent venv 的 python（推荐）
/home/dministrator/projects/hermes-agent/venv/bin/python
```

### 2. 检查包在不同 Python 中的可用性
```python
# 在目标 python 中检查
import sys
print(sys.version)
print(sys.executable)
# 检查特定包
import cv2; print(cv2.__version__)
import numpy; print(numpy.__version__)
```

### 3. 找到可用的 uvicorn/fastapi
```bash
# 常见路径
/home/dministrator/.local/bin/uvicorn     # 系统 python 3.10
/home/dministrator/projects/hermes-agent/venv/bin/python  # hermes venv
```

### 4. 往 hermes-agent venv 装包（venv 没有 pip）
```bash
# 正确方式（venv 没有 pip，用 python -m pip）
/home/dministrator/projects/hermes-agent/venv/bin/python -m pip install fastapi uvicorn python-multipart
# 错误方式（venv/bin/pip 不存在）
/home/dministrator/projects/hermes-agent/venv/bin/pip install ...  # FileNotFoundError
```

### 5. OpenCV LBPH 人脸识别器（无需编译 dlib）
```python
# 正确引入方式
import cv2.face
model = cv2.face.LBPHFaceRecognizer_create(radius=1, neighbors=8, grid_x=8, grid_y=8, threshold=100.0)

# 错误写法（AttributeError）
cv2.LBPHFaceRecognizer_create()       # cv2 没有这个属性
cv2.face_LBPHFaceRecognizer_create()    # 旧版 API 名
```

### 6. Haar 级联分类器路径
```python
cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
detector = cv2.CascadeClassifier(cascade_path)
```

## 常见 Python 环境速查

| 解释器 | 版本 | 路径 | 用途 |
|--------|------|------|------|
| 系统 python3 | 3.10 | /usr/bin/python3 | WSL 默认 |
| hermes-agent venv | 3.11 | ~/projects/hermes-agent/venv/bin/python | 主运行环境 |
| hermes-agent venv + uvicorn | 3.11 | ~/.local/bin/uvicorn | FastAPI 服务 |

## 关键经验（教训）

1. **不要假设 pip 路径存在** — hermes-agent venv 只有 `python -m pip`
2. **不要混用不同 Python 版本的 numpy** — cpython-311 的 .so 无法被 cpython-310 加载
3. **优先用 hermes-agent venv 的 python** — 它的包最完整
4. **OpenCV-contrib 功能用 `cv2.face` 模块** — 不是 `cv2.xxx`
5. **WSL 无 root 时 sudo 会失败** — 此时编译型包（如 dlib）不可用，改用纯 Python/OpenCV 内置方案
