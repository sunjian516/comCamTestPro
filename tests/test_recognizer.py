"""测试人脸识别核心功能"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from core.recognizer import _base64_to_image
from core import face_db

def test_base64_decode():
    import base64, cv2
    arr = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
    _, buf = cv2.imencode(".png", arr)
    b64 = base64.b64encode(buf).decode()
    img = _base64_to_image(b64)
    assert img.shape == (100, 100, 3)
    print("OK base64 decode")

def test_face_db_crud():
    for fid in ["TEST_001", "TEST_002"]:
        face_db.delete_face(fid)
    emb = list(np.random.rand(100).astype(np.float64))
    r = face_db.register_face("TestUser", emb)
    print(f"OK register: {r['face_id']}")
    records = face_db.find_by_name("TestUser")
    print(f"OK find_by_name: {len(records)}")
    r2 = face_db.find_by_face_id(r["face_id"])
    print(f"OK find_by_id: {r2['name']}")
    ok = face_db.delete_face(r["face_id"])
    print(f"OK delete: {ok}")

def test_similarity():
    emb1 = [0.0] * 100
    emb2 = [0.0] * 100
    sim = face_db.compute_similarity(emb1, emb2)
    print(f"OK similarity same vector: {sim}")

if __name__ == "__main__":
    test_face_db_crud()
    test_similarity()
    print("ALL TESTS PASSED")
