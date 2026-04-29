"""
FastAPI 路由：/face/register, /face/compare, /health
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException
from api.schemas import (
    FaceRegisterRequest, FaceRegisterResponse,
    FaceCompareRequest, FaceCompareResponse, FaceMatch,
    FaceAnalyzeRequest, FaceAnalyzeResponse, MaskInfo, EmotionInfo,
    HealthResponse,
)
from core.recognizer import preprocess_image, preprocess_image_color, detect_and_recognize, reload_model
from core.mask_detector import detect_mask
from core.emotion_classifier import classify_emotion
from core import face_db
import base64
from io import BytesIO
from PIL import Image
import numpy as np


router = APIRouter(prefix="/face", tags=["人脸识别"])

# cv2 LBPH 模型自带的 confidence 阈值（越小越严格）
# 同照confidence=0，同一人不同照片约60~90，不同人通常>100
MATCH_THRESHOLD = 100.0


@router.post("/register", response_model=FaceRegisterResponse)
def register(request: FaceRegisterRequest):
    """注册新人脸：单人正脸照，存150x150灰度图，重新训练LBPH模型"""
    face, all_faces = preprocess_image(request.image_base64)
    if face is None:
        raise HTTPException(status_code=400, detail="未检测到人脸，请确保照片中包含清晰正脸")
    if len(all_faces) != 1:
        raise HTTPException(status_code=400, detail=f"检测到{len(all_faces)}张人脸，请确保照片中只有一张清晰正脸")

    # 存150x150原始灰度像素（flattened），用于训练LBPH模型
    pixel_embedding = face.flatten().tolist()
    record = face_db.register_face(request.name, pixel_embedding, request.image_base64)

    # 重新训练模型
    reload_model()

    return FaceRegisterResponse(
        success=True,
        face_id=record["face_id"],
        name=record["name"],
        message=f"注册成功！Face ID: {record['face_id']}，已重新训练模型",
    )


@router.post("/compare", response_model=FaceCompareResponse)
def compare(request: FaceCompareRequest):
    """比对：严格Haar检测 + LBPH模型predict"""
    result, face_count = detect_and_recognize(request.image_base64)
    if result is None:
        return FaceCompareResponse(found=False, face_count=0, all_matches=[])

    confidence = result["confidence"]

    # 过滤无效结果：confidence爆表（LBPH不认识此人）
    # OpenCV对未知人员的confidence会返回1.79e+308
    if confidence > 1e100:
        return FaceCompareResponse(
            found=False,
            top_match=FaceMatch(face_id="", name=result["name"], distance=round(confidence, 2), similarity=0.0, is_match=False),
            all_matches=[],
            face_count=face_count,
        )

    is_match = confidence < MATCH_THRESHOLD

    return FaceCompareResponse(
        found=is_match,
        top_match=FaceMatch(
            face_id="",
            name=result["name"],
            distance=round(confidence, 2),
            similarity=round(1.0 / (1.0 + confidence), 4),
            is_match=is_match,
        ),
        all_matches=[],
        face_count=face_count,
    )


@router.get("/health", response_model=HealthResponse)
def health():
    """健康检查"""
    count = face_db.count_faces()
    return HealthResponse(status="ok", face_count=count, model_loaded=True)


def _base64_to_rgb(base64_str: str) -> np.ndarray:
    """base64 → RGB numpy image"""
    img_bytes = base64.b64decode(base64_str)
    pil_img = Image.open(BytesIO(img_bytes))
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


@router.post("/analyze", response_model=FaceAnalyzeResponse)
def analyze(request: FaceAnalyzeRequest):
    """
    综合人脸分析：
    1. Haar检测人脸
    2. LBPH身份比对
    3. 口罩检测
    4. 表情识别
    """
    result, face_count = detect_and_recognize(request.image_base64)

    # 口罩/表情需要彩色人脸区域，用彩色版预处理
    _, all_faces_color = preprocess_image_color(request.image_base64)

    mask_info = None
    emotion_info = None

    if all_faces_color:
        largest = max(all_faces_color, key=lambda f: f.shape[0] * f.shape[1])
        largest_150 = cv2.resize(largest, (150, 150))
        largest_rgb = cv2.cvtColor(largest_150, cv2.COLOR_BGR2RGB)
        mask_result = detect_mask(largest_rgb)
        mask_info = MaskInfo(**mask_result)
        emotion_result = classify_emotion(largest_rgb)
        emotion_info = EmotionInfo(**emotion_result)

    if result is None:
        return FaceAnalyzeResponse(
            found=False,
            face_count=face_count,
            mask=mask_info,
            emotion=emotion_info,
        )

    confidence = result["confidence"]

    if confidence > 1e100:
        return FaceAnalyzeResponse(
            found=False,
            face_count=face_count,
            face_id="",
            name=result["name"],
            distance=round(confidence, 2),
            similarity=0.0,
            is_match=False,
            mask=mask_info,
            emotion=emotion_info,
        )

    is_match = confidence < MATCH_THRESHOLD

    return FaceAnalyzeResponse(
        found=is_match,
        face_count=face_count,
        face_id="",
        name=result["name"],
        distance=round(confidence, 2),
        similarity=round(1.0 / (1.0 + confidence), 4),
        is_match=is_match,
        mask=mask_info,
        emotion=emotion_info,
    )
