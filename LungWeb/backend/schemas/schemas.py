from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# --- User Schemas ---
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str
    created_at: datetime
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# --- Result Schemas ---

class VLMResponse(BaseModel):
    caption_en: Optional[str]
    caption_vi: Optional[str]
    class Config:
        from_attributes = True

class SegmentationResponse(BaseModel):
    mask_coarse_path: Optional[str]
    mask_lesion_path: Optional[str]
    class Config:
        from_attributes = True

class ImageResponse(BaseModel):
    image_id: int
    filename: str
    file_path: str # URL ảnh PNG để hiển thị
    segmentation: Optional[SegmentationResponse] = None
    vlm_result: Optional[VLMResponse] = None
    class Config:
        from_attributes = True

class ClassificationResponse(BaseModel):
    final_label: str
    final_confidence: float
    detail_probs: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

class CTSeriesResponse(BaseModel):
    series_id: int
    upload_date: datetime
    patient_id: Optional[str]
    
    classification: Optional[ClassificationResponse] = None
    images: List[ImageResponse] = []
    
    class Config:
        from_attributes = True