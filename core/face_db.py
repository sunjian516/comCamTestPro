"""
人脸数据库管理
存储结构：每人一个 {face_id}.json，含128维LBPH特征向量 + 元信息
"""
import json
import os
import random
import string
from pathlib import Path
from datetime import datetime
from typing import Optional
import numpy as np


DB_DIR = Path(__file__).parent.parent / "face_db"
MAX_ID = 9999


def _generate_face_id() -> str:
    existing = set()
    for f in DB_DIR.glob("*.json"):
        try:
            existing.add(int(f.stem.split("_")[1]))
        except Exception:
            pass
    for i in range(1, MAX_ID + 1):
        if i not in existing:
            return f"FACE_{i:04d}"
    raise RuntimeError("人脸库已满（9999人）")


def _load_db() -> dict[str, dict]:
    db = {}
    for path in DB_DIR.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            face_id = data["face_id"]
            db[face_id] = data
        except Exception:
            pass
    return db


def _face_id_to_path(face_id: str) -> Path:
    return DB_DIR / f"{face_id}.json"


def register_face(name: str, embedding: list[float], image_base64: Optional[str] = None) -> dict:
    """注册新人脸，返回记录"""
    face_id = _generate_face_id()
    record = {
        "face_id": face_id,
        "name": name,
        "registered_at": datetime.now().isoformat(),
        "embedding": embedding,
        "image_base64": image_base64,
    }
    with open(_face_id_to_path(face_id), "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    return record


def find_by_face_id(face_id: str) -> Optional[dict]:
    path = _face_id_to_path(face_id)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_by_name(name: str) -> list[dict]:
    return [r for r in _load_db().values() if r["name"] == name]


def get_all_embeddings() -> list[tuple[str, str, list[float]]]:
    """返回所有记录的 (face_id, name, embedding)，统一为1D list"""
    results = []
    for record in _load_db().values():
        emb = record["embedding"]
        # 兼容旧数据：如果是嵌套列表或 numpy array，转为 1D list
        arr = np.array(emb, dtype=np.float64).flatten()
        emb_1d = arr.tolist()
        results.append((record["face_id"], record["name"], emb_1d))
    return results


def delete_face(face_id: str) -> bool:
    path = _face_id_to_path(face_id)
    if path.exists():
        path.unlink()
        return True
    return False


def count_faces() -> int:
    return len(list(DB_DIR.glob("*.json")))


def export_all() -> dict[str, dict]:
    return _load_db()


def compute_similarity(embedding1: list[float], embedding2: list[float]) -> float:
    """计算两个向量的相似度（0~1），使用1/(1+dist)归一化，适用于任意维度的特征向量"""
    arr1 = np.array(embedding1, dtype=np.float64)
    arr2 = np.array(embedding2, dtype=np.float64)
    distance = float(np.linalg.norm(arr1 - arr2))
    # 归一化：1/(1+dist)，distance=0时similarity=1，distance越大similarity越接近0
    return round(float(1.0 / (1.0 + distance)), 4)
