import numpy as np
import cv2
import pydicom
import tensorflow as tf
from tensorflow.keras.applications.resnet50 import preprocess_input as resnet_preprocess
from core.config import settings
import os

def apply_window(img_hu, ww, wl):
    img_min = wl - ww / 2
    img_max = wl + ww / 2
    img = np.clip(img_hu, img_min, img_max)
    if ww == 0: ww = 1
    return ((img - img_min) / ww * 255).astype(np.uint8)

def read_and_window_image(path):
    img_hu = np.zeros((512, 512), dtype=np.float32)
    if path.lower().endswith((".dcm", ".dicom")):
        try:
            dicom = pydicom.dcmread(path, force=True)
            img_hu = dicom.pixel_array.astype(np.float32)
            slope = getattr(dicom, 'RescaleSlope', 1)
            intercept = getattr(dicom, 'RescaleIntercept', 0)
            img_hu = img_hu * slope + intercept
        except: pass
    else:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is not None: 
            img_hu = (img.astype(np.float32) / 255.0) * 2500 - 1000

    img_hu_resized = cv2.resize(img_hu, (settings.IMG_SIZE, settings.IMG_SIZE))
    lung = apply_window(img_hu_resized, ww=1500, wl=-600)
    medi = apply_window(img_hu_resized, ww=350, wl=40)
    canny = cv2.Canny(lung, 100, 200)
    final = cv2.merge([lung, medi, canny])
    return resnet_preprocess(final.astype(np.float32))

class InferenceDataGenerator(tf.keras.utils.Sequence):
    def __init__(self, sequences, batch_size=1):
        self.sequences = sequences
        self.batch_size = batch_size
    
    def __len__(self): 
        return int(np.ceil(len(self.sequences) / self.batch_size))
    
    def __getitem__(self, index):
        batch_seq = self.sequences[index * self.batch_size:(index + 1) * self.batch_size]
        X = []
        for seq_paths in batch_seq:
            seq_imgs = [read_and_window_image(p) for p in seq_paths]
            X.append(np.stack(seq_imgs))
        return np.array(X)

def load_patient_sequences_from_list(file_paths):
    files = sorted(file_paths)
    n = len(files)
    if n < settings.SEQUENCE_LENGTH: return None
    
    target = 20 if n > 30 else 10
    start_idx = max(0, (n - target) // 2)
    center_imgs = files[start_idx : start_idx + target]

    sequences = []
    if len(center_imgs) < settings.SEQUENCE_LENGTH: 
        sequences.append(files[:settings.SEQUENCE_LENGTH]) 
    else:
        for i in range(0, len(center_imgs) - settings.SEQUENCE_LENGTH + 1, 2):
            sequences.append(center_imgs[i : i + settings.SEQUENCE_LENGTH])
    
    if not sequences and len(files) >= settings.SEQUENCE_LENGTH: 
        sequences.append(files[:settings.SEQUENCE_LENGTH])

    return sequences