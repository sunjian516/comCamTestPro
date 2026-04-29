"""
口罩检测模块
纯 OpenCV 经典CV实现，不依赖任何深度学习模型
原理：分析人脸下半脸的纹理 + 颜色分布
"""

import cv2
import numpy as np
from typing import Literal

# 捂脸颜色范围（HSV空间）
_BLUE_LOW  = np.array([90, 40, 40])
_BLUE_HIGH = np.array([130, 255, 255])

# 医用口罩蓝白色HSV范围
_WHITE_LOW  = np.array([0, 0, 140])
_WHITE_HIGH = np.array([180, 40, 255])

# 黑色口罩
_BLACK_LOW  = np.array([0, 0, 0])
_BLACK_HIGH = np.array([180, 255, 60])

# 肤色范围（HSV）
_SKIN_LOW  = np.array([0, 20, 40])
_SKIN_HIGH = np.array([30, 150, 255])


def detect_mask(face_roi_color: np.ndarray) -> dict:
    """
    检测口罩状态

    参数:
        face_roi_color: RGB人脸彩色图（裁剪后的人脸区域）

    返回:
        {
            "status": "no_mask" | "mask" | "partial" | "unknown",
            "confidence": float,         # 0.0~1.0
            "mask_type": "medical" | "cloth" | "black" | "unknown",
            "lower_face_coverage": float  # 下半脸被遮比例 0.0~1.0
        }
    """
    h, w = face_roi_color.shape[:2]
    if h < 20 or w < 20:
        return _unknown_result("人脸区域过小")

    # 分割人脸下半区域（鼻尖到下巴，约占人脸高度40%）
    y_top = int(h * 0.45)
    y_bot = int(h * 0.95)
    lower_face = face_roi_color[y_top:y_bot, :]

    # 转HSV做颜色分析
    hsv = cv2.cvtColor(lower_face, cv2.COLOR_RGB2HSV)

    # 肤色遮盖率（肤色像素占比）：正常未戴口罩的下半脸应该大量肤色
    skin_mask = cv2.inRange(hsv, _SKIN_LOW, _SKIN_HIGH)
    skin_ratio = cv2.countNonZero(skin_mask) / (lower_face.shape[0] * lower_face.shape[1])

    # 蓝色捂脸检测（医用口罩主色）
    blue_mask = cv2.inRange(hsv, _BLUE_LOW, _BLUE_HIGH)
    blue_ratio = cv2.countNonZero(blue_mask) / (lower_face.shape[0] * lower_face.shape[1])

    # 白色捂脸检测
    white_mask = cv2.inRange(hsv, _WHITE_LOW, _WHITE_HIGH)
    white_ratio = cv2.countNonZero(white_mask) / (lower_face.shape[0] * lower_face.shape[1])

    # 黑色捂脸检测
    black_mask = cv2.inRange(hsv, _BLACK_LOW, _BLACK_HIGH)
    black_ratio = cv2.countNonZero(black_mask) / (lower_face.shape[0] * lower_face.shape[1])

    # 纹理分析：口罩区域纹理应该更平滑（方差小）
    gray_lower = cv2.cvtColor(lower_face, cv2.COLOR_RGB2GRAY)
    texture_variance = gray_lower.var()

    # 综合判断
    total_mask_color = blue_ratio + white_ratio + black_ratio

    # 捂脸阈值
    if total_mask_color > 0.25:
        # 有明显口罩色
        if blue_ratio > 0.15:
            mask_type = "medical"
            confidence = min(blue_ratio * 2.5, 0.98)
        elif white_ratio > 0.15:
            mask_type = "cloth"
            confidence = min(white_ratio * 2.5, 0.95)
        elif black_ratio > 0.15:
            mask_type = "black"
            confidence = min(black_ratio * 2.5, 0.95)
        else:
            mask_type = "unknown"
            confidence = min(total_mask_color * 2, 0.90)
        return {
            "status": "mask",
            "confidence": round(confidence, 3),
            "mask_type": mask_type,
            "lower_face_coverage": round(total_mask_color, 3)
        }

    elif skin_ratio > 0.55 and texture_variance > 200:
        # 大量肤色 + 高纹理方差 = 没戴口罩
        return {
            "status": "no_mask",
            "confidence": round(min(skin_ratio * 1.2, 0.97), 3),
            "mask_type": "none",
            "lower_face_coverage": round(skin_ratio, 3)
        }

    elif skin_ratio > 0.30:
        # 部分遮盖（半戴口罩或下巴区域）
        return {
            "status": "partial",
            "confidence": round(min((1 - skin_ratio) * 1.5, 0.88), 3),
            "mask_type": "possible_cloth",
            "lower_face_coverage": round(skin_ratio, 3)
        }

    else:
        # 纹理异常或光照问题
        return _unknown_result(f"texture_var={texture_variance:.0f}, skin={skin_ratio:.2f}")


def _unknown_result(reason: str = "") -> dict:
    return {
        "status": "unknown",
        "confidence": 0.0,
        "mask_type": "unknown",
        "lower_face_coverage": 0.0,
        "reason": reason
    }
