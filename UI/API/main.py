import argparse
from datetime import datetime
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import cv2
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from natsort import natsorted
import numpy as np
from pydantic import BaseModel
import uvicorn
from PIL import Image
from skimage import measure, color, filters
from Resnet.defect_detection import DefectDetection

defectDetection = DefectDetection()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Define a Pydantic model to validate form data
class FeatureExtraction(BaseModel):
    Block1: bool
    Block2: bool
    Block3: bool

class FormData(BaseModel):
    inputImagesFolder: str
    referenceImagesFolder: str
    maskImagesFolder: str
    featureExtraction: FeatureExtraction
    maskExpansionRadius: int
    defectScoreThreshold: int
    defectAreaThreshold: int
    alarmTriggerCount: int
    sampleCount: int

parameters = None

def detect(image_real_path, image_ref_path, image_mask_path, save_folder, lp_value, defect_color, concat_blocks, defect_score_th, defect_area_th):

    os.makedirs(save_folder, exist_ok=True)

    image_real= Image.open(image_real_path)
    image_real = image_real.convert("RGB")
    image_ref= Image.open(image_ref_path)
    image_ref = image_ref.convert("RGB")
    image_mask = Image.open(image_mask_path).convert("L")
    
    binary_mask = np.array(image_mask) > 128
    binary_mask = (binary_mask * 255).astype(np.uint8)
    
    defect_mask, distance_np_image = defectDetection.detect(image_real, image_ref,concat_blocks=concat_blocks)
    defect_mask_crop = cv2.bitwise_and(defect_mask,defect_mask,mask=binary_mask)
    defect_mask_crop[defect_mask_crop < defect_score_th] = 0

    threshold_value = filters.threshold_otsu(defect_mask_crop)  # Otsu's method for automatic thresholding
    binary_image = defect_mask_crop > threshold_value
    labeled_image = measure.label(binary_image, connectivity=2)
    stats = measure.regionprops(labeled_image)

    labeled_image_color = color.label2rgb(labeled_image, bg_label=0, kind='overlay')
    labeled_image_color = (labeled_image_color * 255).astype(np.uint8)

    cv2_image = cv2.cvtColor(np.array(image_real), cv2.COLOR_RGB2BGR)
    has_detect = False
    kernel = np.ones((3, 3), np.uint8)

    for region in stats:  
        if region.area >= defect_area_th:
            has_detect = True
            mask = np.uint8(labeled_image == region.label)  # labels should be a 2D array with labels for each pixel

            dilated_image = cv2.dilate(mask, kernel, iterations=1)
            contours, _ = cv2.findContours(dilated_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(cv2_image, contours, -1, defect_color, 1)
        
    name = lp_value
    
    cv2.imwrite(os.path.join(save_folder, f"score_map_{name}.jpg"), distance_np_image)
    cv2.imwrite(os.path.join(save_folder, f"result_mask_{name}.jpg"), labeled_image_color)
    cv2.imwrite(os.path.join(save_folder, f"final_{name}.jpg"), cv2_image)
    
    def resize_half(image):
        return cv2.resize(image, (image.shape[1] // 2, image.shape[0] // 2))
    
    # cv2.imshow("Pixel-wise Euclidean Distance", resize_half(defect_mask))
    # cv2.imshow("Mask TH", resize_half(labeled_image_color))
    # cv2.imshow("Image result", resize_half(cv2_image))

    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    return has_detect

def extract_sim_lp_value(filename):
    match = re.search(r'Z_lp([0-9\.\-]+)', filename)
    if match:
        return match.group(1).removesuffix(".")
    return None

def extract_lp_value(filename):
    match = re.search(r'Z_lp([0-9\.\-]+)', filename)
    if match:
        return match.group(1).removesuffix(".")
    return None

def extract_mask_z_value(filename):
    match = re.search(r'Z_lp([0-9\.\-]+)', filename)
    if match:
        return match.group(1).removesuffix(".")
    return None

def create_video(save_folder, image_folder,prefix):

    os.makedirs(save_folder,exist_ok=True)
    current_time = datetime.now().strftime("%d_%H_%M_%S")
    
    output_video = f'./{save_folder}/video_{current_time}_{prefix}.mp4' 

    images = [img for img in os.listdir(image_folder) if img.endswith(('.png', '.jpg', '.jpeg')) and img.startswith(prefix)]
    images = natsorted(images)  # Sort images in natural order

    frame = cv2.imread(os.path.join(image_folder, images[0]))
    height, width, layers = frame.shape
    frame_size = (width, height)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # For MP4 format
    video = cv2.VideoWriter(output_video, fourcc, 30, frame_size)  # 30 is the frame rate

    for image in images:
        img_path = os.path.join(image_folder, image)
        frame = cv2.imread(img_path)
        video.write(frame)

    video.release()

    return output_video
    
@app.post("/submit-form")
async def submit_form(data: FormData):
    global parameters
    print("Received Form Data:", data.dict())

    if not data.inputImagesFolder or not data.referenceImagesFolder or not data.maskImagesFolder:
        raise HTTPException(status_code=400, detail="All folder paths must be provided.")

    parameters = data.copy()
    
    concat_blocks = []
    
    if parameters.featureExtraction.Block1:
        concat_blocks.append(1)
    if parameters.featureExtraction.Block2:
        concat_blocks.append(2)
    if parameters.featureExtraction.Block3:
        concat_blocks.append(3)
    
    dst_file_dict = {}
    mask_file_dict = {}

    for dst_file in os.listdir(parameters.referenceImagesFolder):
        dst_lp_value = extract_sim_lp_value(dst_file)
        if dst_lp_value is not None:
            dst_file_dict[dst_lp_value] = os.path.join(parameters.referenceImagesFolder, dst_file)
    
    for mask_file in os.listdir(parameters.maskImagesFolder):
        mask_lp_value = extract_mask_z_value(mask_file)
        if mask_lp_value is not None:
            mask_file_dict[mask_lp_value] = os.path.join(parameters.maskImagesFolder, mask_file)
        
    max_detect = parameters.alarmTriggerCount
    counter = 0

    list_files = os.listdir(parameters.inputImagesFolder)
    selected_files = list_files if data.sampleCount == 0 else list_files[:data.sampleCount]

    time_str = time.strftime("%Y%m%d-%H%M%S")
    save_folder = f"result_resnet_{time_str}"
    
    for img_inpt in selected_files:
        lp_value = extract_lp_value(img_inpt)
        
        if lp_value in dst_file_dict:
            ref_image = dst_file_dict[lp_value]
            mask_image = mask_file_dict[lp_value]
            img_path = os.path.join(parameters.inputImagesFolder, img_inpt)

            blue_color = (255, 0, 0)
            red_color = (0, 0, 255)
        
            has_detect = detect(img_path, ref_image, mask_image, save_folder, lp_value
                                ,blue_color if counter < max_detect else red_color
                                ,concat_blocks=concat_blocks
                                ,defect_score_th=parameters.defectScoreThreshold
                                ,defect_area_th=parameters.defectAreaThreshold)
            
            if has_detect:
                counter += 1

    video_folder = f"result_video_{time_str}"
    videos_score_map = create_video(video_folder, save_folder,"score_map_")
    videos_result_mask = create_video(video_folder, save_folder,"result_mask_")
    videos_final = create_video(video_folder, save_folder,"final_")

    return {
        "message": "Form data received successfully",
        "videos_score_map": videos_score_map,
        "videos_result_mask": videos_result_mask,
        "videos_final": videos_final,
    }

@app.get("/count-images")
async def count_images(folder_path: str):
    try:
        # Validate the folder path
        
        if folder_path == "":
            return {'images_count': 0}
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            raise HTTPException(status_code=400, detail="Invalid folder path")

        # Count image files
        image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff"}
        images_count = sum(1 for file in folder.iterdir() if file.suffix.lower() in image_extensions)

        return {"images_count": images_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/")
def read_root():
    return {"message": "API is running"}

def run_exe():
    # Run the .exe file in the background
    process = subprocess.Popen(["./UI//Defect_Detection_UI.exe"])
    print("The .exe file is running in the background.")

    while process.poll() is None:
        continue
    sys.exit(0)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Defect Detection App arguments")
    parser.add_argument("--ui", type=bool,default=False, help="Show UI App")
    
    args = parser.parse_args()

    print(f"UI: {args.ui}")

    if args.ui:
        exe_thread = threading.Thread(target=run_exe)
        exe_thread.start()

    uvicorn.run(app, host="0.0.0.0", port=8000)