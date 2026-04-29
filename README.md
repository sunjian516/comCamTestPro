# Face Recognition Project

基于 OpenCV LBPH 的人脸注册与比对系统。

## 环境要求
- Python 3.8+
- OpenCV 4.x (opencv-python)
- FastAPI + uvicorn

## 安装
```bash
pip install -r requirements.txt
```

## 启动服务
```bash
cd E:\\her\\workspace\\face_project
python main.py
# 或
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

### 健康检查
GET /face/health

## 微信接入
微信发送图片 -> Hermes -> 调用API -> 返回结果

## 外部项目对接示例
```python
import requests, base64
with open("photo.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()
resp = requests.post("http://localhost:7860/face/compare",
                     json={"image_base64": img_b64})
print(resp.json())
```

## 项目结构
face_project/
  main.py              FastAPI入口
  api/
    routes.py          API路由
    schemas.py          数据模型
  core/
    recognizer.py       人脸识别核心
    face_db.py          人脸库管理
  handlers/
    wechat_handler.py   微信接入
  face_db/              人脸特征库
  tests/
    test_recognizer.py 测试
