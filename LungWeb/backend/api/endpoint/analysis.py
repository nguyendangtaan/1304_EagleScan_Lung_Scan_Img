import os
import uuid
import json
import shutil
from typing import List, Optional, Tuple
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from PIL import Image as PILImage
import numpy as np
import cv2


from core.config import settings
from db.database import get_db
from db.models import CTImage, CTSeries, ClassificationResult, SegmentationResult, VLMResult, User
from services.ml_manager import ml_manager
from api.endpoint.auth import get_current_user
from utils.utils import dicom_to_png_single, dicom_to_png_folder

router = APIRouter()
BASE_URL = "http://127.0.0.1:8000"



def create_session_folder(user_id: int) -> Tuple[str, str]:
   
    session_id = str(uuid.uuid4())
    relative_path = f"{user_id}/{session_id}"
    save_dir = os.path.join(settings.UPLOAD_DIR, relative_path)
    os.makedirs(save_dir, exist_ok=True)
    return save_dir, relative_path

def process_upload_file(file: UploadFile, save_dir: str, relative_path: str, idx: int) -> Tuple[str, Optional[str]]:
    
    ext = file.filename.split('.')[-1].lower()
    
 
    safe_name = f"slice_{idx:03d}.{ext}" if "caption" not in file.filename else f"caption_img.{ext}"
    file_path = os.path.join(save_dir, safe_name)
    
    
    file.file.seek(0)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    display_path = ""
    dcm_path = None

    if ext in ['dcm', 'dicom']:
        dcm_path = file_path
        
        dicom_to_png_single(file_path, save_dir, dicom_mode='CT', color_reversed=True)
        
        
        base_name = os.path.splitext(safe_name)[0]
        possible_png = os.path.join(save_dir, f"{base_name}.png")
        possible_png_frame = os.path.join(save_dir, f"{base_name}_frame_000.png")

        if os.path.exists(possible_png):
            display_path = f"static/uploads/{relative_path}/{base_name}.png"
        elif os.path.exists(possible_png_frame):
            display_path = f"static/uploads/{relative_path}/{base_name}_frame_000.png"
        else:
           
            display_path = f"static/uploads/{relative_path}/{safe_name}"
    else:
        
        display_path = f"static/uploads/{relative_path}/{safe_name}"

    return display_path, dcm_path

def save_mask_image(mask_array: np.ndarray, save_dir: str, prefix: str, idx: int, relative_path: str) -> str:
    
    mask_dir = os.path.join(save_dir, "masks")
    os.makedirs(mask_dir, exist_ok=True)
    
    
    mask = (mask_array > 0.5).astype(np.uint8) * 255
    pil_img = PILImage.fromarray(mask, mode='L')
    
    filename = f"{prefix}_{idx:03d}.png"
    pil_img.save(os.path.join(mask_dir, filename))
    
    return f"static/uploads/{relative_path}/masks/{filename}"



@router.post("/run_classification")
async def run_classification(
    original_files: List[UploadFile] = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        
        save_dir, relative_path = create_session_folder(current_user.user_id)
        
        new_series = CTSeries(user_id=current_user.user_id, folder_path=save_dir, patient_id="Unknown")
        db.add(new_series)
        db.commit()
        db.refresh(new_series)

        saved_dcm_paths = [] 
        
       
        for idx, file in enumerate(original_files):
            display_path, dcm_path = process_upload_file(file, save_dir, relative_path, idx)
            
            
            ai_input_path = dcm_path 
            saved_dcm_paths.append(ai_input_path)

            
            db.add(CTImage(
                series_id=new_series.series_id, 
                filename=file.filename, 
                file_path=display_path, 
                dcm_path=dcm_path, 
                slice_index=idx
            ))
        
        db.commit()

        
        label, conf, probs = ml_manager.predict_classification(saved_dcm_paths)
        
        if not label:
             return {"success": False, "error": "Dữ liệu không đủ để chẩn đoán (Cần tối thiểu 10 ảnh) hoặc lỗi Model."}

       
        result = ClassificationResult(
            series_id=new_series.series_id, 
            final_label=label, 
            final_confidence=float(conf * 100), 
            detail_probs=json.dumps(probs)
        )
        db.add(result)
        db.commit()

        return {
            "success": True, 
            "patient_diagnosis": {
                "final_label": label, 
                "final_confidence": f"{conf*100:.2f}", 
                "mean_probs": {k: f"{v:.2f}" for k,v in probs.items()}
            }
        }
    except Exception as e:
        import traceback; traceback.print_exc()
        return {"success": False, "error": str(e)}


@router.post("/run_segmentation")
async def run_segmentation(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not ml_manager.seg_model:
        return {"success": False, "error": "Model Segmentation chưa được tải."}

    try:
        
        save_dir, relative_path = create_session_folder(current_user.user_id)
        
        new_series = CTSeries(user_id=current_user.user_id, folder_path=save_dir, patient_id="Unknown (Seg)")
        db.add(new_series)
        db.commit()
        db.refresh(new_series)

        results = []

        
        for idx, file in enumerate(files):
            
            display_path, dcm_path = process_upload_file(file, save_dir, relative_path, idx)
            
            
            abs_img_path = os.path.join(settings.UPLOAD_DIR, display_path.replace("static/uploads/", ""))
            
            new_img = CTImage(
                series_id=new_series.series_id,
                filename=file.filename,
                file_path=display_path, 
                dcm_path=dcm_path,
                slice_index=idx
            )
            db.add(new_img)
            db.commit()
            db.refresh(new_img)

            
            try:
                img_pil = PILImage.open(abs_img_path).convert('RGB')
                mask_coarse, mask_lesion = ml_manager.predict_segmentation(img_pil)
                
                
                mc_relative_url = save_mask_image(mask_coarse, save_dir, "coarse", idx, relative_path)
                ml_relative_url = save_mask_image(mask_lesion, save_dir, "lesion", idx, relative_path)

                
                db.add(SegmentationResult(
                    image_id=new_img.image_id,
                    mask_coarse_path=mc_relative_url,
                    mask_lesion_path=ml_relative_url
                ))
                
               
                results.append({
                    "filename": file.filename,
                    "mask_coarse": f"{BASE_URL}/{mc_relative_url}", 
                    "mask_lesion": f"{BASE_URL}/{ml_relative_url}"
                })
            except Exception as e:
                print(f"Lỗi segment ảnh {file.filename}: {e}")
                continue

        db.commit()
        return {"success": True, "results": results}

    except Exception as e:
        import traceback; traceback.print_exc()
        return {"success": False, "error": str(e)}

@router.post("/generate_caption")
async def generate_caption(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not ml_manager.caption_model:
        return {"success": False, "error": "Model Caption chưa được tải."}

    try:
       
        save_dir, relative_path = create_session_folder(current_user.user_id)
        
       
        new_series = CTSeries(user_id=current_user.user_id, folder_path=save_dir, patient_id="Unknown (VLM)")
        db.add(new_series)
        db.commit()
        db.refresh(new_series)

        
        display_path, dcm_path = process_upload_file(file, save_dir, relative_path, idx=0)
        abs_img_path = os.path.join(settings.UPLOAD_DIR, display_path.replace("static/uploads/", ""))

        new_img = CTImage(
            series_id=new_series.series_id,
            filename=file.filename,
            file_path=display_path,
            slice_index=0
        )
        db.add(new_img)
        db.commit()
        db.refresh(new_img)

        
        img_pil = PILImage.open(abs_img_path).convert('RGB')
        eng_cap, vi_cap = ml_manager.generate_caption(img_pil)

        
        db.add(VLMResult(
            image_id=new_img.image_id,
            caption_en=eng_cap,
            caption_vi=vi_cap
        ))
        db.commit()

        return {"success": True, "caption": vi_cap, "caption_en": eng_cap}

    except Exception as e:
        import traceback; traceback.print_exc()
        return {"success": False, "error": str(e)}



@router.post("/convert_dicom_folder")
async def convert_dicom_folder_api(dicom_folder: str = Form(...), output_folder: str = Form(...)):
    try:
        count = dicom_to_png_folder(dicom_folder, output_folder)
        return {"success": True, "converted_count": count}
    except Exception as e: 
        return {"success": False, "error": str(e)}

@router.post("/preview_dcm")
async def preview_dcm(file: UploadFile = File(...)):
   
    import base64
    try:
        temp_dir = "temp_preview"
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}.dcm")
        
        file.file.seek(0)
        with open(temp_path, "wb") as f:
            f.write(await file.read())
            
       
        dicom_to_png_single(temp_path, temp_dir, dicom_mode='CT', color_reversed=True)
        
        
        base_name = os.path.splitext(os.path.basename(temp_path))[0]
        possible_png = os.path.join(temp_dir, f"{base_name}.png")
        if not os.path.exists(possible_png):
            possible_png = os.path.join(temp_dir, f"{base_name}_frame_000.png")
            
        if os.path.exists(possible_png):
            with open(possible_png, "rb") as img_file:
                encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
            
            shutil.rmtree(temp_dir)
            return {"success": True, "png_base64": f"data:image/png;base64,{encoded_string}", "filename": file.filename}
        else:
            shutil.rmtree(temp_dir)
            return {"success": False, "error": "Không thể convert file DICOM này."}
            
    except Exception as e:
        if os.path.exists("temp_preview"): shutil.rmtree("temp_preview")
        return {"success": False, "error": str(e)}