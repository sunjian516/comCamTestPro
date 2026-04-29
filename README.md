# Face Recognition Project

基于 OpenCV LBPH 的人脸注册与比对系统，支持口罩检测与表情分析。

## 环境要求
- Python 3.8+
- OpenCV 4.x (opencv-python)
- scikit-learn
- FastAPI + uvicorn

## 启动服务
```bash
cd /path/to/face_project
uvicorn main:app --host 0.0.0.0 --port 7860
```
服务地址: http://localhost:7860
API文档: http://localhost:7860/docs

## API接口
### 注册人脸
POST /face/register
Body: {"image_base64": "base64字符串", "name": "姓名"}

### 比对人脸
POST /face/compare
Body: {"image_base64": "base64字符串"}

### 综合人脸分析（身份 + 口罩 + 表情）
POST /face/analyze
Body: {"image_base64": "base64字符串"}
返回: {"found", "name", "distance", "mask": {"status", "mask_type", "confidence"}, "emotion": {"emotion", "confidence"}}

### 健康检查
GET /face/health

## 项目结构
face_project/
  main.py              FastAPI入口
  api/
    routes.py          API路由
    schemas.py          数据模型
  core/
    recognizer.py       人脸检测核心（Haar + LBPH）
    face_db.py          人脸库管理
    mask_detector.py    口罩检测（HSV颜色分析）
    emotion_classifier.py 表情识别（几何特征 + SVM）
  handlers/
    wechat_handler.py   微信接入
  face_db/              人脸特征库
  tests/
    test_recognizer.py 测试

## 技术说明
- 口罩检测：基于HSV颜色空间的下半脸分析，区分医用口罩/布口罩/无口罩
- 表情识别：基于面部几何特征 + SVM分类器，支持7种情绪
- 人脸检测：OpenCV Haar级联 + LBPH识别
- 推理引擎：纯CPU，无GPU依赖
