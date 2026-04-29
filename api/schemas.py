from pydantic import BaseModel, Field
from typing import Optional


class FaceRegisterRequest(BaseModel):
    image_base64: str = Field(..., description="图片base64编码")
    name: str = Field(..., description="人员姓名")


class FaceRegisterResponse(BaseModel):
    success: bool
    face_id: str
    name: str
    message: str


class FaceCompareRequest(BaseModel):
    image_base64: str = Field(..., description="图片base64编码")


class FaceMatch(BaseModel):
    face_id: str
    name: str
    distance: float
    similarity: float
    is_match: bool


class FaceCompareResponse(BaseModel):
    found: bool
    top_match: Optional[FaceMatch] = None
    all_matches: list[FaceMatch] = Field(default_factory=list)
    face_count: int


class MaskInfo(BaseModel):
    status: str = Field(description="no_mask | mask | partial | unknown")
    confidence: float
    mask_type: str = Field(description="medical | cloth | black | none | unknown")
    lower_face_coverage: float


class EmotionInfo(BaseModel):
    emotion: str = Field(description="happy | sad | angry | fear | surprise | disgust | neutral")
    confidence: float
    method: str = Field(description="geometric | simple | heuristic")


class FaceAnalyzeRequest(BaseModel):
    image_base64: str = Field(..., description="图片base64编码")


# 单人人脸分析结果（供多脸/批量返回使用）
class SingleFaceResult(BaseModel):
    face_id: str = ""
    name: str = ""
    distance: float = 0.0
    similarity: float = 0.0
    is_match: bool = False
    mask: Optional[MaskInfo] = None
    emotion: Optional[EmotionInfo] = None


# 单张图片分析响应（支持多脸）
class FaceAnalyzeResponse(BaseModel):
    face_count: int
    faces: list[SingleFaceResult] = Field(default_factory=list)
    # ⚠️ 以下字段为兼容旧版保留（仅当 face_count=1 时有意义）
    found: bool = False
    face_id: str = ""
    name: str = ""
    distance: float = 0.0
    similarity: float = 0.0
    is_match: bool = False
    mask: Optional[MaskInfo] = None
    emotion: Optional[EmotionInfo] = None


# 批量分析请求（一次提交多帧）
class BatchAnalyzeRequest(BaseModel):
    images_base64: list[str] = Field(..., description="多张图片base64列表，最大50张")
    skip_no_face: bool = Field(default=True, description="跳过无人脸的帧")


class BatchAnalyzeResponse(BaseModel):
    total_frames: int
    processed_frames: int
    results: list[FaceAnalyzeResponse]


class HealthResponse(BaseModel):
    status: str
    face_count: int
    model_loaded: bool
