"""
FastAPI 路由：/face/register, /face/compare, /face/analyze, /face/analyze/batch, /health
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
    SingleFaceResult, BatchAnalyzeRequest, BatchAnalyzeResponse,
    HealthResponse,
)
from core.recognizer import (
    preprocess_image, preprocess_image_color,
    detect_and_recognize_all, reload_model, _get_model, _labels,
)
from core.mask_detector import detect_mask
from core.emotion_classifier import classify_emotion
from core import face_db
import base64
from io import BytesIO
from PIL import Image
import numpy as np


router = APIRouter(prefix="/face", tags=["人脸识别"])

MATCH_THRESHOLD = 100.0


# ──────────────────────────────────────────────
# 辅助函数
# ──────────────────────────────────────────────

def _base64_to_image(base64_str: str) -> np.ndarray:
    """base64 → BGR numpy image"""
    img_bytes = base64.b64decode(base64_str)
    pil_img = Image.open(BytesIO(img_bytes))
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def _analyze_face(face_bgr: np.ndarray) -> SingleFaceResult:
    """对单个人脸 BGR ROI 进行身份+口罩+表情分析，返回 SingleFaceResult"""
    # 身份识别：灰度化后 LBPH predict
    face_gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
    face_150 = cv2.resize(face_gray, (150, 150))

    model = _get_model()
    label, confidence = model.predict(face_150.astype(np.float64))
    name = _labels.get(label, f"Unknown_{label}")

    # 口罩 + 表情：需要 RGB + 150x150
    face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
    face_rgb_150 = cv2.resize(face_rgb, (150, 150))

    mask_result = detect_mask(face_rgb_150)
    mask_info = MaskInfo(**mask_result)

    emotion_result = classify_emotion(face_rgb_150)
    emotion_info = EmotionInfo(**emotion_result)

    is_match = confidence < MATCH_THRESHOLD

    return SingleFaceResult(
        face_id="",
        name=name,
        distance=round(float(confidence), 2),
        similarity=round(1.0 / (1.0 + confidence), 4),
        is_match=is_match,
        mask=mask_info,
        emotion=emotion_info,
    )


# ──────────────────────────────────────────────
# 注册
# ──────────────────────────────────────────────

@router.post("/register", response_model=FaceRegisterResponse)
def register(request: FaceRegisterRequest):
    """注册新人脸：单人正脸照，存150x150灰度图，重新训练LBPH模型"""
    face, all_faces = preprocess_image(request.image_base64)
    if face is None:
        raise HTTPException(status_code=400, detail="未检测到人脸，请确保照片中包含清晰正脸")
    if len(all_faces) != 1:
        raise HTTPException(status_code=400, detail=f"检测到{len(all_faces)}张人脸，请确保照片中只有一张清晰正脸")

    pixel_embedding = face.flatten().tolist()
    record = face_db.register_face(request.name, pixel_embedding, request.image_base64)
    reload_model()

    return FaceRegisterResponse(
        success=True,
        face_id=record["face_id"],
        name=record["name"],
        message=f"注册成功！Face ID: {record['face_id']}，已重新训练模型",
    )


# ──────────────────────────────────────────────
# 比对
# ──────────────────────────────────────────────

@router.post("/compare", response_model=FaceCompareResponse)
def compare(request: FaceCompareRequest):
    """比对：严格Haar检测 + LBPH模型predict"""
    result, face_count = detect_and_recognize_all(request.image_base64)
    if result is None:
        return FaceCompareResponse(found=False, face_count=0, all_matches=[])

    confidence = result["confidence"]
    if confidence > 1e100:
        return FaceCompareResponse(
            found=False, face_count=face_count,
            top_match=FaceMatch(face_id="", name=result["name"], distance=round(confidence, 2), similarity=0.0, is_match=False),
            all_matches=[],
        )

    is_match = confidence < MATCH_THRESHOLD
    return FaceCompareResponse(
        found=is_match,
        top_match=FaceMatch(face_id="", name=result["name"], distance=round(confidence, 2),
                            similarity=round(1.0 / (1.0 + confidence), 4), is_match=is_match),
        all_matches=[],
        face_count=face_count,
    )


# ──────────────────────────────────────────────
# 综合分析（多脸）
# ──────────────────────────────────────────────

@router.post("/analyze", response_model=FaceAnalyzeResponse)
def analyze(request: FaceAnalyzeRequest):
    """
    综合人脸分析（支持多脸）：
    1. Haar检测所有人脸
    2. 每人脸分别做身份比对 + 口罩检测 + 表情识别
    3. 返回所有检测到的人脸结果
    """
    # 获取所有人脸（灰度 + 彩色）
    gray_faces, color_faces = _extract_all_faces(request.image_base64)
    face_count = len(gray_faces)

    if face_count == 0:
        return FaceAnalyzeResponse(face_count=0, faces=[], found=False)

    # 每人脸独立分析
    results: list[SingleFaceResult] = []
    for bf in color_faces:
        results.append(_analyze_face(bf))

    # 兼容旧版：第一个人的信息放在顶层字段
    top = results[0]

    return FaceAnalyzeResponse(
        face_count=face_count,
        faces=results,
        found=top.is_match,
        face_id=top.face_id,
        name=top.name,
        distance=top.distance,
        similarity=top.similarity,
        is_match=top.is_match,
        mask=top.mask,
        emotion=top.emotion,
    )


# ──────────────────────────────────────────────
# 批量分析（多帧）
# ──────────────────────────────────────────────

@router.post("/analyze/batch", response_model=BatchAnalyzeResponse)
def analyze_batch(request: BatchAnalyzeRequest):
    """
    批量帧分析：一次提交多张图片，逐一分析并汇总结果。
    适用于监控视频抽帧批量处理。
    """
    images = request.images_base64
    if len(images) > 50:
        raise HTTPException(status_code=400, detail="单次最多支持50张图片")

    batch_results: list[FaceAnalyzeResponse] = []
    processed = 0

    for b64 in images:
        gray_faces, color_faces = _extract_all_faces(b64)
        face_count = len(gray_faces)

        if face_count == 0 and request.skip_no_face:
            # 跳过无人脸帧，结果不计入
            continue

        processed += 1
        if face_count == 0:
            batch_results.append(FaceAnalyzeResponse(face_count=0, faces=[], found=False))
            continue

        face_results: list[SingleFaceResult] = []
        for bf in color_faces:
            face_results.append(_analyze_face(bf))

        top = face_results[0]
        batch_results.append(FaceAnalyzeResponse(
            face_count=face_count,
            faces=face_results,
            found=top.is_match,
            face_id=top.face_id,
            name=top.name,
            distance=top.distance,
            similarity=top.similarity,
            is_match=top.is_match,
            mask=top.mask,
            emotion=top.emotion,
        ))

    return BatchAnalyzeResponse(
        total_frames=len(images),
        processed_frames=processed,
        results=batch_results,
    )


# ──────────────────────────────────────────────
# 内部函数：从 base64 提取所有人脸（灰度 + 彩色）
# ──────────────────────────────────────────────

def _extract_all_faces(base64_str: str, scale: float = 0.5):
    """
    从图片中提取所有人脸区域。
    返回: (gray_faces: list[np.ndarray], color_faces: list[np.ndarray])
    """
    img = _base64_to_image(base64_str)
    H, W = img.shape[:2]

    if scale < 1.0:
        img_small = cv2.resize(img, (int(W * scale), int(H * scale)))
    else:
        img_small = img

    gray_small = cv2.cvtColor(img_small, cv2.COLOR_BGR2GRAY)
    gray_full = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    from core.recognizer import _get_detector
    detector = _get_detector()
    min_size = (max(25, int(50 * scale)), max(25, int(50 * scale)))
    faces = detector.detectMultiScale(gray_small, scaleFactor=1.15, minNeighbors=5, minSize=min_size)

    if len(faces) == 0:
        return [], []

    gray_faces, color_faces = [], []
    for fx, fy, fw, fh in sorted(faces, key=lambda f: f[2] * f[3], reverse=True):
        if scale < 1.0:
            fx, fy, fw, fh = int(fx / scale), int(fy / scale), int(fw / scale), int(fh / scale)
        gray_faces.append(gray_full[int(fy):int(fy) + int(fh), int(fx):int(fx) + int(fw)])
        color_faces.append(img[int(fy):int(fy) + int(fh), int(fx):int(fx) + int(fw)])

    return gray_faces, color_faces


# ──────────────────────────────────────────────
# 健康检查
# ──────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
def health():
    from core.face_db import DB_DIR
    from pathlib import Path
    face_count = len(list(Path(DB_DIR).glob("*.json")))
    return HealthResponse(
        status="running",
        face_count=face_count,
        model_loaded=_get_model() is not None,
    )
