import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    PROJECT_NAME: str = "Lung Cancer AI API"
    API_V1_STR: str = "/api/v1"
    
   
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 * 24 * 60

  
    UPLOAD_DIR: str = "static/uploads"
    

    BINARY_MODEL_PATH: str = str(BASE_DIR / "model" / "classification" / "GRU" / "binary_best.h5")
    TRI_MODEL_PATH: str = str(BASE_DIR / "model" / "classification" / "GRU" / "tri_best.h5")
    SEG_MODEL_PATH: str = str(BASE_DIR / "model" / "segment" / "unet_segmentation.h5")
    CAPTION_MODEL_PATH: str = str(BASE_DIR / "model" / "blip_model_final")

    
    SEQUENCE_LENGTH: int = 10
    IMG_SIZE: int = 224
    BATCH_SIZE: int = 8

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)