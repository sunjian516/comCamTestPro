"""
人脸识别服务入口
FastAPI + uvicorn
启动：python main.py 或 uvicorn main:app --reload --port 7860
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as face_router

app = FastAPI(
    title="Face Recognition API",
    version="1.0.0",
    description="人脸注册与比对服务，支持微信图片接入",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(face_router)


@app.get("/", tags=["默认"])
def root():
    return {
        "service": "Face Recognition API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "注册人脸": "POST /face/register",
            "比对人脸": "POST /face/compare",
            "健康检查": "GET /face/health",
        },
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7860, reload=False)
