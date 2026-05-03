---
name: face-recognition-project
description: 基于 OpenCV LBPH + FastAPI + Haar 级联的人脸识别系统，含性能优化实践
---
# Face Recognition Project

基于 OpenCV LBPH + FastAPI + Haar 级联的人脸识别系统。

## 项目路径
`/home/dministrator/her_workspace/face_project/`

## 技术栈
- **人脸检测**：OpenCV Haar级联分类器（`cv2.CascadeClassifier`）
- **特征提取+比对**：OpenCV 内置 `cv2.face.LBPHFaceRecognizer_create()` + `model.predict()`
- **API框架**：FastAPI + uvicorn
- **Python环境**：`/home/dministrator/projects/hermes-agent/venv/bin/python`

## 启动命令
```bash
cd /home/dministrator/her_workspace/face_project
/home/dministrator/projects/hermes-agent/venv/bin/uvicorn main:app --host 0.0.0.0 --port 7860
```
注意：启动路径是 `main:app` 不是 `api.main:app`。

## API接口
| 端点 | 方法 | 说明 |
|------|------|------|
| `/face/register` | POST | 注册人脸：`{"image_base64": "...", "name": "姓名"}` |
| `/face/compare` | POST | 比对人脸：`{"image_base64": "..."}` |
| `/face/health` | GET | 健康检查 |

## 性能数据（基准）
| 阶段 | 优化前 | 优化后 | 提速 |
|------|--------|--------|------|
| Haar 人脸检测 | ~210ms/图 | ~72ms/图 | **2.9x** |
| LBPH 模型推理 | ~1.6ms/次 | ~1.6ms/次 | 1x |
| 整体 API | ~222ms/次 | ~63ms/次 | **3.5x** |

## 性能优化方案

### 1. Haar 参数调优（最优配置）
```python
# 优化前：sf=1.1, mn=6 → 慢（每层缩放10%，候选框多）
# 优化后：sf=1.15, mn=5 → 快38%，检测结果完全一致
faces = detector.detectMultiScale(gray,
    scaleFactor=1.15,   # 原1.1，每层缩放15%更少计算
    minNeighbors=5,      # 原6，容忍更多重叠候选框
    minSize=(50, 50))
```

### 2. 图片降采样策略（3x提速关键）
Haar 检测图片面积而非内容，降采样50%可提速2x且检测结果不变：
```python
SCALE = 0.5
img_small = cv2.resize(img, (int(W * SCALE), int(H * SCALE)))
faces = detector.detectMultiScale(gray_small,
    scaleFactor=1.15, minNeighbors=5,
    minSize=(max(25, int(50 * SCALE)), max(25, int(50 * SCALE))))
```

### 3. 坐标映射（降采样必须同时修复裁剪）
**⚠️ 关键bug**：降采样后不能用缩放图的坐标裁剪原图！
```python
# 错误！小图坐标超出大图边界 → 人脸区域错误 → LBPH比对完全失败
face_roi = gray_small[scaled_x:scaled_x+w, scaled_y:scaled_y+h]  # ❌

# 正确：小图检测 → 坐标÷scale映射回原图 → 从原图裁剪
x_orig = int(x_s / SCALE)
y_orig = int(y_s / SCALE)
w_orig = int(w_s / SCALE)
h_orig = int(h_s / SCALE)
face_roi = gray_full[y_orig:y_orig+h_orig, x_orig:x_orig+w_orig]  # ✅
```
**现象**：用降采样但未修复坐标映射时，LBPH confidence 会爆表（1.79e+308），因为裁出来的是错误区域。

### 完整检测+裁剪代码模板
```python
def detect_and_crop(img, scale=0.5):
    H, W = img.shape[:2]
    img_small = cv2.resize(img, (int(W*scale), int(H*scale)))
    gray_small = cv2.cvtColor(img_small, cv2.COLOR_BGR2GRAY)
    gray_full = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    min_size = (max(25, int(50*scale)), max(25, int(50*scale)))
    faces = detector.detectMultiScale(gray_small, scaleFactor=1.15, minNeighbors=5, minSize=min_size)

    if len(faces) == 0:
        return None

    x_s, y_s, w_s, h_s = max(faces, key=lambda f: f[2]*f[3])
    if scale < 1.0:
        x, y, w, h = int(x_s/scale), int(y_s/scale), int(w_s/scale), int(h_s/scale)
    else:
        x, y, w, h = x_s, y_s, w_s, h_s

    face_roi = gray_full[y:y+h, x:x+w]  # 从原图裁剪！
    return cv2.resize(face_roi, (150, 150))
```

## 比对阈值（基于实测）
- `MATCH_THRESHOLD = 100.0`（用于 LBPH confidence，confidence越小越像）
- 同一人同照：confidence = 0.0
- 同一人不同照片：confidence ≈ 60~95（阈值100可兼容）
- 陌生人/非人脸：confidence ≥ 1.79e+308（LBPH 对未知返回1.79e+308）
- **阈值 100.0 是 cv2 LBPH 模型专用**，不能用旧阈值 8.0（那是手动LBP直方图时代的）

## 人脸库存储
`face_db/` 目录下每人一个 JSON 文件：
```json
{
  "face_id": "FACE_0001",
  "name": "孙剑",
  "registered_at": "2026-04-28T20:31:55",
  "embedding": [0.0, ...],  // 22500维，150×150灰度像素flattened
  "image_base64": "..."
}
```

## 依赖
已装在 hermes-agent venv：fastapi, uvicorn, python-multipart, opencv-python(=4.10.0), numpy(=1.26.4), scikit-learn(=1.8.0)

## 微信图片测试方法
`vision_analyze` 对本地缓存的微信图片失效，用 requests 直接调 API：
```python
import base64, requests
with open("/home/dministrator/.hermes/cache/images/img_xxx.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()
resp = requests.post("http://localhost:7860/face/compare", json={"image_base64": img_b64}, timeout=15)
print(resp.json())
```

## 核心踩坑记录

### 0. `face_db` 导入遗漏导致 500（2026-04-30）
`recognizer.py` 的 `load_histograms()` 调用 `face_db.get_all_embeddings()`，但模块顶部忘记 `from core import face_db`。
症状：`/face/health` 返回 500 Internal Server Error，日志 `NameError: name 'face_db' is not defined`。
修复：`from core import face_db` 加到 `core/recognizer.py` 顶部。

### 1. 降采样后坐标映射bug（2026-04-29）
降采样后用 `gray_small` 的坐标直接裁剪原图 `gray_full` → 越界/错误区域 → LBPH confidence 爆表。
**修复**：检测用小图，坐标必须除以 scale 映射回原图后从原图裁剪。

### 2. LBPH 模型需先 train() 再 predict()
`cv2.face.LBPHFaceRecognizer_create().predict()` 需要先 `train()`。
全局模型在 `_get_model()` 中懒加载，首次注册后通过 `reload_model()` 重新训练。

### 3. 未知人员 confidence = 1.79e+308
cv2 LBPH 对不认识的人返回极大值，不是普通浮点数。
**必须用** `confidence > 1e100` 判断是否是有效识别结果，否则会把 `1.79e+308` 当作正常 confidence 返回。

### 4. 多人照判定
比对时遇到多人照，`detectMultiScale` 会返回多个框，取最大（面积）的那个进行比对。
如果最大脸不是数据库里的人，会返回 `Unknown_-1` + `confidence=1.79e+308`。
比对接口对 `confidence > 1e100` 返回 `found=False`（视为不认识/陌生人）。

### 5. 非人脸（物体/风景）拒绝
Haar 检测不到人脸时 `detectMultiScale` 返回空列表，`face_count=0` → 接口直接返回 `found=False`。
这是第一道防线，比 LBPH 还早触发。

### 6. 人脸数据库只有1条记录时训练bug
只有1个人脸时，`cv2.face.LBPHFaceRecognizer.train()` 仍可正常工作（label_array = np.array([1], dtype=np.int32)）。
关键是要正确构建 `_labels` 字典并在 predict 后用 `.get()` 查询。

### 7. 启动路径是 main:app
uvicorn 启动命令写 `api.main` 会报 `ModuleNotFoundError`。
正确：`uvicorn main:app`，且需要 cd 到项目根目录。

### 8. pip install 大包超时处理
- PyTorch CPU 版约 760MB，pip install 多次超时（300s、600s、7200s 均失败/cancelled）
- MediaPipe 安装超时 60s
- GitHub raw/ModelScope 下载 ONNX 模型文件也会 connection refused
- **最终方案**：经典 OpenCV 方法（HSV 颜色分析 + 几何特征），无需下载任何外部模型
- **教训**：hermes-agent venv 环境 pip 依赖安装尽量用小包；网络不通时优先考虑无需模型的经典CV

## 未来视频流接入
监控摄像头 → FFmpeg 抽帧 → HTTP POST `/face/compare` → 报警。
参考 `skill_view("face-recognition-project")` 获取详细架构图。

## 口罩检测 + 表情识别（已实现，2026-04-29）

### 最终方案：经典CV路线（无PyTorch）
原计划用 PyTorch/DL，因网络问题（见下文"踩坑记录"）改为纯 OpenCV 经典方法。

**实现文件**：
- `core/mask_detector.py` — HSV 颜色空间分析下脸区域，区分医用/布料/黑色/不戴口罩
- `core/emotion_classifier.py` — 几何特征（眼/眉/嘴距离角度）+ SVM 分类 7 种表情
- `api/routes.py` — 新增 `POST /face/analyze` 接口，合并人脸比对 + 口罩 + 表情
- `api/schemas.py` — 新增 `MaskInfo`/`EmotionInfo` Pydantic 模型

**新接口**：`POST /face/analyze`
```json
{
  "image_base64": "...",
  "include_emotion": true,
  "include_mask": true
}
```
返回：`{"identity": {...}, "mask": {...}, "emotion": {...}, "face_count": N}`

### 性能数据
| 阶段 | 速度 |
|------|------|
| Haar 人脸检测 | ~72ms/图 |
| 口罩检测（HSV分析）| <1ms |
| 表情识别（几何特征+SVM）| <2ms |
| 整体 `/face/analyze` | ~80ms/图 |

### 关键 bug 及修复

**Bug 1：颜色预处理导致口罩检测失效**
- 原因：`preprocess_image()` 返回灰度图（LBPH 需要），`routes.py` 用 `cv2.COLOR_GRAY2RGB` 转为假彩色，再转 HSV 后所有通道值相同
- 修复：新增 `preprocess_image_color()` 函数，返回原图裁剪的人脸区域

**Bug 2：表情分类器 ROI 缩放导致分数全零**
- 原因：`_simple_emotion_heuristic()` 使用相对比例（0.82×宽、0.60×高）设计假设输入 150px。直接输入 Haar 检测的 548px 大脸时，`int(0.82*548) < int(0.60*548)` → mouth_region 为空 → 返回全零分数 → 默认 surprise
- 修复：routes 在调用 emotion_classifier 前将 ROI 统一 resize 到 150×150

**Bug 3：SVM predict 与 predict_proba 结果不一致**
- 原因：`svm.predict()` 使用决策函数（原始距离），`svm.predict_proba()` 使用 Platt 缩放（概率）。对某张照片 `predict()` 返回 "happy"，但 `predict_proba` 最大概率是 "surprise"（0.196 vs 0.151）
- 修复：用 `max(probs)` 而非 `svm.predict()` 作为最终输出

### 已知局限
- **表情分类不准**：几何特征无法区分 surprise/neutral/happy（用户选择暂不改进）
- **口罩检测**：HSV 颜色分析对极端光照可能失效

### 硬件环境限制
- **GPU**：GTX 750 Ti 2GB，WSL GPU直通未通（`/dev/nvidia0` 不存在）
- **网络**：PyPI ✅ 可访问；HuggingFace ❌、GitHub raw ❌、ModelScope ❌（connection refused）

## 升级规划（未完成）
- 人脸检测：从 Haar 升级到 DNN（需能下载 ONNX 模型）
- 表情识别：改用深度学习模型（需 PyTorch 安装成功或能下载 ONNX）
- 口罩检测：可考虑升级到 DL 分类器
