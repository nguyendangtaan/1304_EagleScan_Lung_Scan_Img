import os
import tensorflow as tf
import torch
import numpy as np
from transformers import BlipProcessor, BlipForConditionalGeneration
from deep_translator import GoogleTranslator
from core.config import settings
from services.ml_architectures import build_gru_model, seg_custom_objects
from services.image_processing import load_patient_sequences_from_list, InferenceDataGenerator

class MLModelManager:
    def __init__(self):
        self.binary_model = None
        self.tri_model = None
        self.seg_model = None
        self.caption_model = None
        self.caption_processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.target_names_bin = ["Normal", "Abnormal"]
        self.target_names_tri = ["Adenocarcinoma", "Small Cell Carcinoma", "Squamous Cell Carcinoma"]

    def load_models(self):
       
       
        try:
            print(f"Checking Binary Model: {settings.BINARY_MODEL_PATH}")
            if os.path.exists(settings.BINARY_MODEL_PATH):
                print("   File exists, loading...")
                self.binary_model = build_gru_model(num_classes=2)
                self.binary_model.load_weights(settings.BINARY_MODEL_PATH)
                print(" Binary Model Loaded Successfully")
            else:
                print(f"   File not found at: {settings.BINARY_MODEL_PATH}")
            
            print(f"🔍 Checking Tri-class Model: {settings.TRI_MODEL_PATH}")
            if os.path.exists(settings.TRI_MODEL_PATH):
                print("   File exists, loading...")
                self.tri_model = build_gru_model(num_classes=3)
                self.tri_model.load_weights(settings.TRI_MODEL_PATH, by_name=True, skip_mismatch=True)
                print(" Tri-class Model Loaded Successfully")
            else:
                print(f"   File not found at: {settings.TRI_MODEL_PATH}")
        except Exception as e:
            import traceback
            print(f" Classification Load Error: {e}")
            print(f"   Traceback: {traceback.format_exc()}")

        
        try:
            print(f"Checking Segmentation Model: {settings.SEG_MODEL_PATH}")
            if os.path.exists(settings.SEG_MODEL_PATH):
                print("   File exists, loading...")
                self.seg_model = tf.keras.models.load_model(settings.SEG_MODEL_PATH, custom_objects=seg_custom_objects)
                print(" Segmentation Model Loaded Successfully")
            else:
                print(f"   File not found at: {settings.SEG_MODEL_PATH}")
        except Exception as e:
            import traceback
            print(f" Segmentation Load Error: {e}")
            print(f"   Traceback: {traceback.format_exc()}")

        # 3. Caption Model
        try:
            print(f" Checking Caption Model: {settings.CAPTION_MODEL_PATH}")
            if os.path.exists(settings.CAPTION_MODEL_PATH):
                print("   Local model found, loading...")
                path = settings.CAPTION_MODEL_PATH
            else:
                print(f"    Local model not found, using HuggingFace: {settings.CAPTION_MODEL_PATH}")
                path = "Salesforce/blip-image-captioning-base"
            
            self.caption_processor = BlipProcessor.from_pretrained(path)
            self.caption_model = BlipForConditionalGeneration.from_pretrained(path)
            self.caption_model.to(self.device)
            print(" Caption Model Loaded Successfully")
        except Exception as e:
            import traceback
            print(f"Caption Load Error: {e}")
            print(f"   Traceback: {traceback.format_exc()}")

        # Summary
        print("\n Model Loading Summary:")
        print(f"   Binary Model: {'✅' if self.binary_model else '❌'}")
        print(f"   Tri-class Model: {'✅' if self.tri_model else '❌'}")
        print(f"   Segmentation Model: {'✅' if self.seg_model else '❌'}")
        print(f"   Caption Model: {'✅' if self.caption_model else '❌'}")

    def predict_classification(self, file_paths):
        sequences = load_patient_sequences_from_list(file_paths)
        if not sequences or not self.binary_model or not self.tri_model:
            return None, None

        gen = InferenceDataGenerator(sequences, settings.BATCH_SIZE)
        
        # Binary prediction
        preds_bin = self.binary_model.predict(gen, verbose=0)
        conf_bin = np.max(preds_bin, axis=1, keepdims=True)
        w_avg_bin = np.sum(preds_bin * conf_bin, axis=0) / (np.sum(conf_bin) + 1e-7)
        label_idx = np.argmax(w_avg_bin)
        
        result_probs = {"Normal": float(w_avg_bin[0]*100), "Abnormal": float(w_avg_bin[1]*100)}
        final_label = self.target_names_bin[label_idx]
        final_conf = w_avg_bin[label_idx]

        # Tri-class if Abnormal
        if label_idx == 1:
            preds_tri = self.tri_model.predict(gen, verbose=0)
            conf_tri = np.max(preds_tri, axis=1, keepdims=True)
            w_avg_tri = np.sum(preds_tri * conf_tri, axis=0) / (np.sum(conf_tri) + 1e-7)
            tri_idx = np.argmax(w_avg_tri)
            
            final_label = self.target_names_tri[tri_idx]
            final_conf = w_avg_tri[tri_idx]
            result_probs = {
                "Adenocarcinoma": float(w_avg_tri[0]*100),
                "Small Cell Carcinoma": float(w_avg_tri[1]*100),
                "Squamous Cell Carcinoma": float(w_avg_tri[2]*100)
            }
        
        return final_label, final_conf, result_probs

    def predict_segmentation(self, img_pil):
        if not self.seg_model: return None, None
        img_input = np.array(img_pil.resize((256, 256))) / 255.0
        mc, ml = self.seg_model.predict(np.expand_dims(img_input, axis=0), verbose=0)
        return np.squeeze(mc), np.squeeze(ml)

    def generate_caption(self, img_pil):
        if not self.caption_model: return None, None
        inputs = self.caption_processor(images=img_pil, return_tensors="pt").to(self.device)
        ids = self.caption_model.generate(**inputs, max_length=100, num_beams=5, early_stopping=True)
        eng = self.caption_processor.batch_decode(ids, skip_special_tokens=True)[0]
        try: vi = GoogleTranslator(source='auto', target='vi').translate(eng)
        except: vi = eng
        return eng, vi

ml_manager = MLModelManager()