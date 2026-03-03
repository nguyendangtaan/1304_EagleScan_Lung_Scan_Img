from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base

# --- 1. Bảng User ---
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Quan hệ: Một User có nhiều CTSeries (Bệnh án)
    series = relationship("CTSeries", back_populates="owner")

# --- 2. Bảng CTSeries  ---
class CTSeries(Base):
    __tablename__ = "ct_series"

    series_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id")) 
    
    patient_id = Column(String, nullable=True, default="Unknown") 
    folder_path = Column(String, nullable=False) # Đường dẫn thư mục gốc trên server
    upload_date = Column(DateTime, default=datetime.utcnow)

    # Quan hệ
    owner = relationship("User", back_populates="series")
    images = relationship("CTImage", back_populates="series", cascade="all, delete-orphan")
    classification = relationship("ClassificationResult", back_populates="series", uselist=False)

# --- 3. Bảng CTImage ---
class CTImage(Base):
    __tablename__ = "ct_images"

    image_id = Column(Integer, primary_key=True, index=True)
    series_id = Column(Integer, ForeignKey("ct_series.series_id"))
    
    filename = Column(String, nullable=False) 
    file_path = Column(String, nullable=False)
    dcm_path = Column(String, nullable=True)   
    slice_index = Column(Integer, nullable=True) 

    # Quan hệ
    series = relationship("CTSeries", back_populates="images")
    segmentation = relationship("SegmentationResult", back_populates="image", uselist=False)
    vlm_result = relationship("VLMResult", back_populates="image", uselist=False)

# --- 4. Bảng ClassificationResult  ---
class ClassificationResult(Base):
    __tablename__ = "classification_results"

    result_id = Column(Integer, primary_key=True, index=True)
    series_id = Column(Integer, ForeignKey("ct_series.series_id"))

    final_label = Column(String, nullable=False) 
    final_confidence = Column(Float, nullable=False)
    detail_probs = Column(Text, nullable=True) # Lưu JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

    series = relationship("CTSeries", back_populates="classification")

# --- 5. Bảng SegmentationResult  ---
class SegmentationResult(Base):
    __tablename__ = "segmentation_results"

    seg_id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("ct_images.image_id"))

    mask_coarse_path = Column(String, nullable=True) 
    mask_lesion_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    image = relationship("CTImage", back_populates="segmentation")

# --- 6. Bảng VLMResult  ---
class VLMResult(Base):
    __tablename__ = "vlm_results"

    vlm_id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("ct_images.image_id"))

    caption_en = Column(Text, nullable=True)
    caption_vi = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    image = relationship("CTImage", back_populates="vlm_result")