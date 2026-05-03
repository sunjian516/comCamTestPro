---
name: global-state-synchronization
description: 多模块共享内存数据时，集中管理全局状态以避免读写不同步的bug
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [architecture, python, global-state, debugging]
    related_skills: [systematic-debugging]
---

# 全局状态集中管理规范

## 问题场景

多模块共享同一份内存数据集时（如缓存、直方图库、人脸数据库等），如果每个模块各自维护一份全局变量副本，容易出现**写入和读取不同步**的bug——一个模块写入，另一毫不相关的模块读取，永远读到空或旧数据。

**典型案例**：人脸识别项目中 `routes.py` 和 `recognizer.py` 都定义了 `_face_id_to_histogram = {}`，`compare_by_histogram()` 写入 `recognizer._face_id_to_histogram`，`/compare` 接口从 `routes._face_id_to_histogram` 读取，结果永远返回空列表。

## 规范

### 核心原则

> **一份数据，只在一个模块中定义和修改。**

### 具体规则

1. **加载函数放在一个模块**：`load_xxx()` 只在一个模块中定义
2. **全局变量只在一个模块**：定义和修改集中在一个模块
3. **其他模块引用而非复制**：
   - 方案A：直接引用定义模块的变量，如 `recognizer._face_id_to_histogram`
   - 方案B：通过 getter 函数访问，不直接引用模块级变量
4. **初始化时机明确**：在 app startup 事件中统一加载，不要在各请求 handler 中分散加载

### Python 实践

```python
# ── bad.py ──
# routes.py
_face_id_to_histogram = {}  # ❌ routes自己维护一份副本

def _load_histograms():
    global _face_id_to_histogram
    for face_id, name, emb in face_db.get_all():
        _face_id_to_histogram[face_id] = np.array(emb)

def compare(...):
    hist = _face_id_to_histogram[...]  # ❌ 读自己的副本，recognizer写入另一份

# recognizer.py
_face_id_to_histogram = {}  # ❌ 又一份副本

def compare_by_histogram(...):
    global _face_id_to_histogram
    _face_id_to_histogram[...] = hist  # 写到自己这份，读写不同步
```

```python
# ── good.py ──
# recognizer.py（集中管理）
_face_id_to_histogram = {}  # 唯一真相源

def load_histograms():
    """唯一加载入口"""
    global _face_id_to_histogram
    _face_id_to_histogram = {}
    for face_id, name, emb in face_db.get_all():
        _face_id_to_histogram[face_id] = np.array(emb)

def compare_by_histogram(...):
    """使用全局变量，读写都在同一个模块"""
    global _face_id_to_histogram
    # ...

# routes.py（只使用，不维护）
from core import recognizer

@app.on_event("startup")
def startup():
    recognizer.load_histograms()  # 启动时统一加载

def compare(...):
    hist = recognizer._face_id_to_histogram[...]  # ✅ 引用而非复制
```

## 验证方法

修改后，用集成测试（TestClient 或 curl）完整走一遍"写入→读取"流程，确认数据能流通：

```python
# 写入
response = client.post("/register", files={"image": ...})
# 读取
response = client.post("/compare", json={"image": ...})
assert response.json()["matches"]  # 不为空则通过
```

## 触发条件

任何涉及多模块共享内存数据集的改动，都应回顾此规范。
