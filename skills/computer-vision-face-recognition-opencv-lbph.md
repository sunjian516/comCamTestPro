---
name: face-recognition-opencv-lbph
description: OpenCV LBPH 人脸识别系统开发经验——阈值设置、Haar参数、模型方法选择
---

# OpenCV LBPH 人脸识别系统开发经验

## 背景

基于 OpenCV LBPH (Local Binary Patterns Histograms) 做人脸识别系统，用于微信场景：用户发照片→判断是否为孙剑本人。

## 核心技术决策

### 方案选择：用 cv2 LBPH 模型自带的 predict()

**错误做法**：手动提取 LBP 特征→计算直方图→欧氏距离
- 用 `cv2.face.LBPHFaceRecognizer_create()` 训练模型后，手动实现 `_simple_lbp()` 计算直方图，然后用 L2 distance 比对
- 问题：直方图维度不匹配（训练用原始像素，推理用直方图），阈值无科学依据

**正确做法**：用模型自带的 `predict()` 方法
- 注册时：Haar检测→灰度→150×150→展平→`model.train()`（训练数据是原始像素）
- 比对时：Haar检测→灰度→150×150→展平→`model.predict()`→返回 `{label, confidence}`
- cv2 LBPH 的 `predict()` 返回的 confidence 是业界标准，比自创的距离公式可靠得多

### 阈值设置（基于实测数据）

| 场景 | confidence 范围 |
|------|----------------|
| 同一人完全相同照片 | 0.0 |
| 同一人不同照片 | ~60~90（实测88.48） |
| 陌生人脸 | 1.79e+308（float max，即 DBL_MAX） |

**阈值**：MATCH_THRESHOLD = 100.0
- 太小（如60）会误拒本人
- 太大无必要，因为陌生人脸 confidence 直接爆表

### Haar 检测参数

```python
cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)
# 检测参数
detector.detectMultiScale(
    gray, scaleFactor=1.1, minNeighbors=6,
    minSize=(50, 50),  # ← 关键：50×50，不是30×30
    maxSize=(500, 500)
)
```

**minSize=50 而非 30**：
- 旧照片人脸小（如68×68），30会检出一堆小误报
- 50能有效过滤噪声检测

**minNeighbors=6**：
- 控制检测质量，太低→多误报，太高→漏检

## 关键教训

### 1. 必须用模型原生方法做比对
手动实现 LBP → 直方图 → 距离 的链条看似透明，实际上丢了模型训练时用的特征空间。
cv2 LBPH 的 `predict()` 在训练时建立了 LBPH 特征空间，推理必须用同一空间。

### 2. 陌生人脸的 confidence 是 1.79e+308
这是 `np.finfo(np.float64).max`，不是普通的"很大数字"。
判断逻辑：
```python
if confidence > 1e+100:  # 实际是 > DBL_MAX 的判断
    return "unknown"
```

### 3. 必须处理多人照片
注册和比对时，如果 `len(all_faces) != 1` 应该拒绝：
```python
if len(all_faces) != 1:
    raise HTTPException(status_code=400, detail="需单人正脸")
```
这样多人物照片直接过滤掉，不会产生错误匹配。

### 4. 延迟来源要分清
比对接口本身只需 ~0.8 秒，延迟主要在 vision_analyze（10-30秒）。

## 性能数据

| 操作 | 耗时 |
|------|------|
| Haar 人脸检测 | ~0.1-0.3s |
| LBPH predict 比对 | ~0.01-0.05s |
| vision_analyze（视觉AI） | ~10-30s |
| 总接口延迟 | 0.8-1s（不含vision）|

## 项目结构

```
/home/dministrator/her_workspace/face_project/
├── api/routes.py          # API路由（register/compare/health）
├── core/recognizer.py     # 核心识别（Haar检测 + LBPH模型）
├── core/face_db.py         # 人脸数据库（JSON存储）
└── face_db/                # 人脸记录（FACE_XXXX.json）
    └── FACE_0001.json      # 孙剑，150×150原始像素flattened
```

## 阈值调优记录

| 日期 | 阈值 | 改动原因 | 结果 |
|------|------|---------|------|
| 第一轮 | 60.0 | 基于旧版LBP直方图距离 | 误报严重（电瓶车判为本人） |
| 第二轮 | 8.0 | 调低以容纳LBP距离范围 | 仍误报，方向错误 |
| 最终 | 100.0 | 切换到LBPH model.predict()，基于实测数据 | 全部通过 |

## 相关文件

- `recognizer.py` 的核心函数：`detect_and_recognize()`, `_get_model()`, `_get_detector()`
- `routes.py` 的核心常量：`MATCH_THRESHOLD = 100.0`
