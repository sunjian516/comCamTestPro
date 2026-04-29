"""
人脸识别核心模块
使用 OpenCV LBPH 算法 + Haar 级联检测器
"""
import cv2
import numpy as np
from typing import Optional
import base64
from io import BytesIO
from pathlib import Path
from PIL import Image


# 全局单例（延迟加载）
_detector: Optional[cv2.CascadeClassifier] = None
_model: Optional[cv2.face.LBPHFaceRecognizer] = None
_labels: dict[int, str] = {}


def _get_detector() -> cv2.CascadeClassifier:
    global _detector
    if _detector is None:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _detector = cv2.CascadeClassifier(cascade_path)
        if _detector.empty():
            raise RuntimeError(f"无法加载级联分类器: {cascade_path}")
    return _detector


def _get_model() -> cv2.face.LBPHFaceRecognizer:
    """获取已训练的LBPH模型（Lazy loading + 首次自动训练）"""
    global _model, _labels
    if _model is None:
        _train_lbph_model()
    return _model


def _train_lbph_model():
    """扫描face_db所有人脸，注册到LBPH模型并训练"""
    global _model, _labels
    from core.face_db import DB_DIR

    faces, labels = [], {}
    label_counter = [0]

    def next_label():
        label_counter[0] += 1
        return label_counter[0]

    for p in sorted(Path(DB_DIR).glob("*.json")):
        try:
            import json
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            emb = np.array(data["embedding"], dtype=np.float64)
            face_roi = emb.reshape(150, 150)
            name = data["name"]
            label = next_label()
            faces.append(face_roi)
            labels[label] = name
        except Exception:
            pass

    if not faces:
        _model = cv2.face.LBPHFaceRecognizer_create(radius=1, neighbors=8, grid_x=8, grid_y=8, threshold=100.0)
        _labels = {}
        return

    _labels = labels
    _model = cv2.face.LBPHFaceRecognizer_create(radius=1, neighbors=8, grid_x=8, grid_y=8, threshold=100.0)
    _model.train([f.astype(np.float64) for f in faces], np.array(list(labels.keys())))


def reload_model():
    """重新训练模型（注册新人脸后调用）"""
    global _model
    _model = None
    _get_model()


def _base64_to_image(base64_str: str) -> np.ndarray:
    """base64字符串 → OpenCV BGR图像"""
    img_bytes = base64.b64decode(base64_str)
    pil_img = Image.open(BytesIO(img_bytes))
    img_rgb = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    return img_rgb


def preprocess_image(base64_str: str, scale: float = 0.5) -> tuple[Optional[np.ndarray], list]:
    """
    预处理：base64 → 人脸检测 → 灰度归一化。
    返回: (归一化人脸区域图像 或 None, 所有检测到的人脸区域列表)
    """
    img = _base64_to_image(base64_str)
    H, W = img.shape[:2]

    if scale < 1.0:
        img_small = cv2.resize(img, (int(W * scale), int(H * scale)))
    else:
        img_small = img

    gray_small = cv2.cvtColor(img_small, cv2.COLOR_BGR2GRAY)
    gray_full = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    detector = _get_detector()
    min_size = (max(25, int(50 * scale)), max(25, int(50 * scale)))
    faces = detector.detectMultiScale(gray_small, scaleFactor=1.15, minNeighbors=5, minSize=min_size)
    if len(faces) == 0:
        return None, []

    x_s, y_s, w_s, h_s = max(faces, key=lambda f: f[2] * f[3])
    if scale < 1.0:
        x, y, w, h = int(x_s / scale), int(y_s / scale), int(w_s / scale), int(h_s / scale)
    else:
        x, y, w, h = x_s, y_s, w_s, h_s

    face_roi = gray_full[int(y):int(y) + int(h), int(x):int(x) + int(w)]
    face_resized = cv2.resize(face_roi, (150, 150))
    all_faces_roi = []
    for fx, fy, fw, fh in sorted(faces, key=lambda f: f[2] * f[3], reverse=True):
        if scale < 1.0:
            fx, fy, fw, fh = int(fx / scale), int(fy / scale), int(fw / scale), int(fh / scale)
        all_faces_roi.append(gray_full[int(fy):int(fy) + int(fh), int(fx):int(fx) + int(fw)])

    return face_resized, all_faces_roi


def preprocess_image_color(base64_str: str, scale: float = 0.5) -> tuple[Optional[np.ndarray], list]:
    """预处理（彩色版）：返回 BGR 人脸彩色图，供口罩/表情分析用。"""
    img = _base64_to_image(base64_str)
    H, W = img.shape[:2]

    if scale < 1.0:
        img_small = cv2.resize(img, (int(W * scale), int(H * scale)))
    else:
        img_small = img

    gray_small = cv2.cvtColor(img_small, cv2.COLOR_BGR2GRAY)
    detector = _get_detector()
    min_size = (max(25, int(50 * scale)), max(25, int(50 * scale)))
    faces = detector.detectMultiScale(gray_small, scaleFactor=1.15, minNeighbors=5, minSize=min_size)
    if len(faces) == 0:
        return None, []

    all_faces_color = []
    for fx, fy, fw, fh in sorted(faces, key=lambda f: f[2] * f[3], reverse=True):
        if scale < 1.0:
            fx, fy, fw, fh = int(fx / scale), int(fy / scale), int(fw / scale), int(fh / scale)
        all_faces_color.append(img[int(fy):int(fy) + int(fh), int(fx):int(fx) + int(fw)])

    return None, all_faces_color


def detect_and_recognize(base64_str: str, scale: float = 0.5) -> tuple[Optional[dict], int]:
    """
    完整人脸识别流程（最大人脸）：Haar检测 → LBPH predict。
    返回: ({"label": int, "name": str, "confidence": float} 或 None, 检测到的人脸数)
    """
    img = _base64_to_image(base64_str)
    H, W = img.shape[:2]

    if scale < 1.0:
        img_small = cv2.resize(img, (int(W * scale), int(H * scale)))
    else:
        img_small = img

    gray_small = cv2.cvtColor(img_small, cv2.COLOR_BGR2GRAY)
    gray_full = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    detector = _get_detector()
    min_size = (max(25, int(50 * scale)), max(25, int(50 * scale)))
    faces = detector.detectMultiScale(gray_small, scaleFactor=1.15, minNeighbors=5, minSize=min_size)
    face_count = len(faces)
    if face_count == 0:
        return None, 0

    x_s, y_s, w_s, h_s = max(faces, key=lambda f: f[2] * f[3])
    if scale < 1.0:
        x, y, w, h = int(x_s / scale), int(y_s / scale), int(w_s / scale), int(h_s / scale)
    else:
        x, y, w, h = x_s, y_s, w_s, h_s

    face_roi = gray_full[int(y):int(y) + int(h), int(x):int(x) + int(w)]
    face_resized = cv2.resize(face_roi, (150, 150))

    model = _get_model()
    label, confidence = model.predict(face_resized.astype(np.float64))
    name = _labels.get(label, f"Unknown_{label}")

    return {"label": int(label), "name": name, "confidence": float(confidence)}, face_count


def detect_and_recognize_all(base64_str: str, scale: float = 0.5) -> tuple[Optional[dict], int]:
    """
    完整人脸识别流程（第一人）：Haar检测 → LBPH predict（第一人脸）。
    与 detect_and_recognize 区别：返回值结构一致，但内部检测逻辑统一。
    返回: ({"label": int, "name": str, "confidence": float} 或 None, 检测到的人脸数)
    """
    return detect_and_recognize(base64_str, scale)


def get_label_name(label: int) -> str:
    return _labels.get(label, f"Unknown_{label}")
