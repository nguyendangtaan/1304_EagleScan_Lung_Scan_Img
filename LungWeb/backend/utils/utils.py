import os
import cv2
import numpy as np
import pydicom as dicomio
import SimpleITK as sitk
from PIL import Image




def loadFile(filename):
    ds = sitk.ReadImage(filename)
    img_array = sitk.GetArrayFromImage(ds)
    if len(img_array.shape) == 3:
        frame_num, width, height = img_array.shape
        ch = 1
        return img_array, frame_num, width, height, ch
    elif len(img_array.shape) == 4:
        frame_num, width, height, ch = img_array.shape
        return img_array, frame_num, width, height, ch




def MatrixToImage(data, ch):
    # data = (data+1024)*0.125
    # new_im = Image.fromarray(data.astype(np.uint8))
    # new_im.show()
    if ch == 3:
        img_rgb = cv2.cvtColor(data, cv2.COLOR_BGR2RGB)
    if ch == 1:
        data = (data + 1024) * 0.125
        img_rgb = data.astype(np.uint8)
    return img_rgb


def PETToImage(img_array, color_reversed=True):
    info = np.finfo(img_array.dtype)
    data = img_array.astype(np.float64(1)) / np.max(img_array)
    if color_reversed is True:
        data = 255 - 255 * data
    elif color_reversed is False:
        data = 255 * data
    # data = (data + 1024) * 0.125
    img = data.astype(np.uint8)
    img = np.transpose(img, (1, 2, 0))
    # cv2.imshow('test', img)
    return img


def dicom_to_png_single(dicom_path, output_path, dicom_mode='CT', color_reversed=True):
    
 
    try:
        # Đọc file DICOM
        img_array, frame_num, width, height, ch = loadFile(dicom_path)
        
        # Xử lý từng frame (lát cắt)
        for frame_idx in range(frame_num):
            if dicom_mode == 'CT':
                # Xử lý CT
                if len(img_array.shape) == 3:
                    frame_data = img_array[frame_idx]
                else:
                    frame_data = img_array[frame_idx, :, :, 0] if ch == 1 else img_array[frame_idx]
                img_bitmap = MatrixToImage(frame_data, ch)
            elif dicom_mode == 'PET':
                # Xử lý PET
                if len(img_array.shape) == 3:
                    frame_data = img_array[frame_idx:frame_idx+1]
                else:
                    frame_data = img_array[frame_idx:frame_idx+1]
                img_bitmap = PETToImage(frame_data, color_reversed=color_reversed)
            else:
                print(f"Unknown dicom_mode: {dicom_mode}")
                return False
            
            # Nếu là grayscale, chuyển sang BGR để lưu PNG
            if len(img_bitmap.shape) == 2:
                img_bitmap = cv2.cvtColor(img_bitmap, cv2.COLOR_GRAY2BGR)
            elif len(img_bitmap.shape) == 3 and img_bitmap.shape[2] == 1:
                img_bitmap = cv2.cvtColor(img_bitmap, cv2.COLOR_GRAY2BGR)
            
            # Tạo tên file output
            base_name = os.path.splitext(os.path.basename(dicom_path))[0]
            if frame_num > 1:
                output_filename = f"{base_name}_frame_{frame_idx:03d}.png"
            else:
                output_filename = f"{base_name}.png"
            
            output_filepath = os.path.join(output_path, output_filename)
            
            # Lưu file PNG
            cv2.imwrite(output_filepath, img_bitmap)
            print(f"Đã chuyển đổi: {dicom_path} -> {output_filepath}")
        
        return True
    except Exception as e:
        print(f"Lỗi khi chuyển đổi {dicom_path}: {str(e)}")
        return False


def dicom_to_png_folder(dicom_folder, output_folder, dicom_mode='CT', color_reversed=True, recursive=True):
    
    os.makedirs(output_folder, exist_ok=True)
    
    # Đếm số file đã chuyển đổi
    converted_count = 0
    
    # Hàm đệ quy để tìm tất cả file .dcm
    def find_dicom_files(folder, file_list):
        items = os.listdir(folder)
        for item in items:
            item_path = os.path.join(folder, item)
            if os.path.isfile(item_path) and (item.lower().endswith('.dcm') or item.lower().endswith('.dicom')):
                file_list.append(item_path)
            elif os.path.isdir(item_path) and recursive:
                find_dicom_files(item_path, file_list)
    
    # Tìm tất cả file DICOM
    dicom_files = []
    find_dicom_files(dicom_folder, dicom_files)
    dicom_files.sort()  # Sắp xếp để xử lý theo thứ tự
    
    print(f"Tìm thấy {len(dicom_files)} file DICOM trong {dicom_folder}")
    
    # Chuyển đổi từng file
    for dicom_file in dicom_files:
        # Tạo tên thư mục con trong output dựa trên cấu trúc thư mục gốc
        relative_path = os.path.relpath(dicom_file, dicom_folder)
        relative_dir = os.path.dirname(relative_path)
        
        if relative_dir:
            # Tạo thư mục con trong output
            output_subdir = os.path.join(output_folder, relative_dir)
            os.makedirs(output_subdir, exist_ok=True)
        else:
            output_subdir = output_folder
        
        # Chuyển đổi file
        if dicom_to_png_single(dicom_file, output_subdir, dicom_mode, color_reversed):
            converted_count += 1
    
    print(f"\nHoàn thành! Đã chuyển đổi {converted_count}/{len(dicom_files)} file DICOM sang PNG")
    return converted_count