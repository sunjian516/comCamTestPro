"""微信图片接收处理模块"""
import base64
from core.recognizer import preprocess_image
from core import face_db


def handle_wechat_image(image_base64: str, name: str = None) -> dict:
    """
    处理微信发来的图片
    1. 如果传了 name -> 注册新人脸
    2. 如果没传 name -> 比对所有人脸库
    """
    embedding, face_count = preprocess_image(image_base64)
    if embedding is None:
        return {"success": False, "error": "未检测到人脸"}
    
    if face_count > 1:
        return {"success": False, "error": f"检测到{face_count}张人脸，请确保只有一张"}
    
    if name:
        record = face_db.register_face(name, embedding, image_base64)
        return {
            "success": True,
            "action": "register",
            "face_id": record["face_id"],
            "name": record["name"],
            "message": f"注册成功！ID: {record['face_id']}",
        }
    else:
        all_emb = face_db.get_all_embeddings()
        if not all_emb:
            return {"success": False, "error": "人脸库为空，请先注册"}
        
        import numpy as np
        best_match = None
        best_dist = float("inf")
        for face_id, person_name, stored_emb in all_emb:
            dist = float(np.linalg.norm(
                np.array(embedding, dtype=np.float64) -
                np.array(stored_emb, dtype=np.float64)
            ))
            if dist < best_dist:
                best_dist = dist
                best_match = (face_id, person_name, dist)
        
        face_id, person_name, dist = best_match
        is_match = dist < 60.0
        sim = face_db.compute_similarity(embedding, stored_emb)
        
        return {
            "success": True,
            "action": "compare",
            "found": is_match,
            "face_id": face_id,
            "name": person_name,
            "distance": round(dist, 2),
            "is_match": is_match,
        }
