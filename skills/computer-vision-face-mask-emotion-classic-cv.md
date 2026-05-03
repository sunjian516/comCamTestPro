---
name: face-mask-emotion-classic-cv
description: 纯 OpenCV 经典CV实现口罩检测+表情识别，无需PyTorch/深度学习模型，完全离线运行
tags: [opencv, face-detection, mask-detection, emotion-classification, cpu-only]
---

# 口罩检测 + 表情识别（纯 OpenCV 经典CV方案）

## 背景
WSL GPU不可用、网络无法下载PyTorch/HuggingFace环境下，为人脸识别系统添加口罩检测和表情识别。纯经典CV，完全离线。

## 架构

```
输入图片 → Haar人脸检测 → 裁剪彩色人脸ROI
                              ↓
              ┌──────────────┴──────────────┐
              ↓                              ↓
      口罩检测（下半脸HSV分析）      表情分类（几何特征+概率SVM）
```

## 核心模块

| 文件 | 功能 |
|------|------|
| `core/mask_detector.py` | 口罩检测（HSV颜色+纹理方差分析） |
| `core/emotion_classifier.py` | 表情分类（几何特征+概率SVM） |
| `core/recognizer.py` | 人脸检测识别，新增 `preprocess_image_color()` |
| `api/routes.py` | `/face/analyze` 综合分析接口 |

## 关键实现细节

### 口罩检测
- 下半脸（y: 45%~95%），HSV颜色分析
- 肤色比例 > 0.55 → 无口罩；口罩色比例 > 0.25 → 有口罩
- **输入必须是真实彩色图**，灰度转RGB会导致HSV分析失效

### 表情分类
- 12维几何特征（眼/眉/嘴/对称性）
- SVM RBF核，probability=True
- **用 `np.argmax(probs)` 取最高概率类，禁止用 `svm.predict()`**（decision_function和概率可能不一致）

### 重要教训
- `preprocess_image()` 返回灰度ROI（给LBPH用）
- 口罩/表情分析**必须**用 `preprocess_image_color()`（裁剪自原始彩色图）
- 从灰度图 `cv2.COLOR_GRAY2RGB` 只是复制通道，HSV分析会完全失效

### 关键Bug
1. **灰度图HSV失效**：灰度转RGB后HSV全是灰度值 → 新增 `preprocess_image_color()`
2. **SVM predict vs 概率不一致**：用 `np.argmax(probs)` 代替 `svm.predict()`
3. **ROI尺寸不一致**：统一 resize 到 150x150
4. **字节码缓存**：修改 .py 后删除 `__pycache__` 再重启

## API

```
POST /face/analyze
返回: {found, face_count, name, distance, is_match,
       mask: {status, confidence, mask_type, lower_face_coverage},
       emotion: {emotion, confidence, method, all_scores}}
```

## 局限
- 表情分类："严肃/neutral/happy/surprise"容易混淆（经典CV固有局限）
- Haar对侧脸/小脸检测效果弱

## 依赖
- opencv-python >= 4.10
- scikit-learn >= 1.8
- onnxruntime >= 1.25（预留）
- fastapi + uvicorn

纯 OpenCV 经典 CV 实现口罩检测 + 表情识别，**完全不依赖 PyTorch/TensorFlow/ONNX 模型下载**，适合网络受限/离线环境。

## 适用场景
- 网络不稳定，无法下载大型模型文件（HuggingFace/GitHub 常见被墙）
- 电脑配置低（GTX 750 Ti 等老 GPU），PyTorch 安装困难
- 需要秒启动、无外部依赖的人脸属性分析

## 核心结论

| 指标 | 深度学习方案 | 经典 CV 方案 |
|------|------------|-------------|
| 精度 | 高 | 中等 |
| 离线可用性 | ❌ 需下载模型 | ✅ 完全离线 |
| 启动速度 | 慢（加载大模型） | 秒启 |
| 网络依赖 | HuggingFace/GitHub | 无 |

**推荐策略**：经典 CV 先跑起来，等网络稳定或换好机器再上深度学习。

---

## 口罩检测（core/mask_detector.py）

### 原理
分析人脸**下半脸区域**的：
1. **HSV 颜色分布** — 蓝色（医用）、白色（布）、黑色口罩各有特征
2. **肤色占比** — 口罩遮盖区域肤色像素减少
3. **纹理方差** — 口罩区域比真实皮肤更平滑

### 关键代码逻辑

```python
# HSV 分量检测
hsv = cv2.cvtColor(lower_face, cv2.COLOR_RGB2HSV)
blue_mask  = cv2.inRange(hsv, [90,40,40], [130,255,255])  # 医用蓝
white_mask = cv2.inRange(hsv, [0,0,140], [180,40,255])   # 白色布
black_mask = cv2.inRange(hsv, [0,0,0], [180,255,60])       # 黑色

# 肤色占比（正常未戴口罩下半脸肤色比例高）
skin_mask = cv2.inRange(hsv, [0,20,40], [30,150,255])
skin_ratio = countNonZero(skin_mask) / area

# 综合判断
if total_mask_color > 0.25:  → mask
elif skin_ratio > 0.55 and texture_variance > 200:  → no_mask
elif skin_ratio > 0.30:  → partial
```

### 返回格式
```python
{"status": "mask", "confidence": 0.95, "mask_type": "medical", "lower_face_coverage": 0.88}
# status: no_mask | mask | partial | unknown
# mask_type: medical | cloth | black | none | unknown
```

### 局限性
- 对相似肤色背景可能误报，阈值需根据实际场景调整
- 精度约 75-85%，不如深度学习

---

## 表情识别（core/emotion_classifier.py）

### 降级路径（3级）

**Level 1 — SVM + 几何特征（需 sklearn）**
- 68 个面部关键点 → 提取 12 维几何特征（FACS 启发）
- 用 jaii/FER2013 风格合成数据训练 SVM（代码内置，无需下载）

**Level 2 — 图像处理 + 启发式规则**
- 无关键点模型时，用 Sobel/亮度/对称性等图像特征
- 7 类表情的加权评分

**Level 3 — 最简规则（无依赖）**
```python
scores["happy"]    = corner_lift * 0.4 + eye_brightness * 0.3 + mouth_edge * 0.3
scores["surprise"] = mouth_opening * 0.5 + eye_open * 0.3
scores["angry"]     = brow_dark * 0.5 + asymmetry * 0.3
```

### 返回格式
```python
{"emotion": "happy", "confidence": 0.151, "method": "simple", "all_scores": {...}}
# emotion: happy | sad | angry | fear | surprise | disgust | neutral
# method: geometric | simple | heuristic
```

---

## 依赖

仅需 OpenCV + NumPy + scikit-learn：
```bash
pip install opencv-python numpy scikit-learn
```

---

## 关键踩坑记录（4条）

### Bug 1: 灰度图转"彩色"后 HSV 分析失效
**现象**：口罩一直误报为"mask"，但直接调 `detect_mask()` 却正常。
**根因**：`preprocess_image` 返回灰度图，路由里用 `cv2.COLOR_GRAY2RGB` 只是把灰度值复制到3通道，HSV 的 S/V 通道还是灰度信息。颜色判断完全失效。
**修复**：新增 `preprocess_image_color()` 直接从原始 BGR 图裁剪人脸，而不是从灰度图。

```python
# 错误 ❌ — GRBG2RGB 复制的是灰度值，不是真彩色
largest_rgb = cv2.cvtColor(largest, cv2.COLOR_GRAY2RGB)

# 正确 ✅ — 从原始彩色图裁剪
largest_rgb = cv2.cvtColor(largest_150, cv2.COLOR_BGR2RGB)
```

### Bug 2: SVM predict() 和 predict_proba() 结果不一致
**现象**：表情分类置信度取错，明明概率最高的是 surprise，但返回的是 happy。
**根因**：`svm.predict()` 用 decision function（基于超平面距离），`svm.predict_proba()` 用 Platt scaling 概率回归。两者可能对同一个样本给出不同的"预测类"。
**修复**：用 `argmax(probs)` 取概率最高的类，不用 `predict()` 的结果。

```python
probs = svm.predict_proba(features_scaled)[0]
best_class = int(np.argmax(probs))  # ✅ 用概率最高的类
return {"emotion": _svm_labels[best_class], "confidence": float(probs[best_class]), ...}
```

### Bug 3: 人脸 ROI 尺寸没归一化
**现象**：表情分析时 mouth_region 数组为空（NaN）。
**根因**：Haar 返回的 ROI 是原始尺寸（如 548px），但 `_simple_emotion_heuristic` 里的系数 `int(h*0.60)` ~ `int(h*0.82)` 是按 150px 设计的。原始尺寸下 `0.60*548 > 0.82*548`，切片顺序反了，数组越界变成 0。
**修复**：统一 resize 到 150x150 再分析。

```python
largest_150 = cv2.resize(largest, (150, 150))  # 先归一化
largest_rgb = cv2.cvtColor(largest_150, cv2.COLOR_BGR2RGB)
```

### Bug 4: 服务重启后 .py 修改不生效
**现象**：改了代码，但 API 行为没变。
**根因**：Python 会缓存 `.pyc` 字节码，修改 `.py` 文件后必须清除。
**修复**：

```bash
find . -name '__pycache__' -type d -exec rm -rf {} +
lsof -ti:7860 | xargs kill -9
```

## 已知问题 & 调试经验

### 口罩误报
- 蓝色背景/衣服可能触发"medical mask"误检
- 解决：增加肤色占比前置检查，`skin_ratio > 0.2` 再考虑判为口罩

### 表情置信度低
- 经典 CV 方法表情置信度普遍偏低（0.1-0.3），这是正常的
- "严肃/neutral" 和 "sad/fear" 在几何特征上非常接近，难以区分是当前方案的固有局限

### 关键点模型缺失
- `_estimate_landmarks_from_face()` 是手动估算的均值关键点
- 如有 Dlib 的 `shape_predictor_68_face_landmarks.dat` 可直接替代 Level 1

---

## 文件位置
```
/home/dministrator/her_workspace/face_project/core/
├── mask_detector.py        # 口罩检测
├── emotion_classifier.py   # 表情分类
└── recognizer.py          # 人脸识别（原有 Haar+LBPH）
```

---

## 网络环境备注

| 地址 | 可访问性 | 用途 |
|------|---------|------|
| PyPI | ✅ | pip 安装 |
| modelscope.cn | ✅ | 备用镜像 |
| HuggingFace | ❌ | 模型下载 |
| GitHub raw | ❌ | 模型下载 |
| download.pytorch.org | ❌ | PyTorch 下载 |

PyTorch Linux **无独立 CPU 索引**，CUDA 版含 GPU 驱动降级后约 760MB，安装极慢/超时。
