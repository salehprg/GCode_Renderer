import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog
from Resnet.defect_detection import DefectDetection
from PIL import Image
from skimage import measure, color, filters

# Callback function for the trackbars (not used, but needed for createTrackbar)
def nothing(x):
    pass

# Initialize Tkinter (used only for file dialog)
root = tk.Tk()
root.withdraw()  # Hide the root Tkinter window

image_real_path = "Images\Set2\In\img_2024-11-27T07-11-43.300Z_lp38.jpg"
image_ref_path = "Images\Set2\Ref\img_2024-11-26T22-59-58.937Z_lp38.jpg"
image_mask_path = "Images\Set2\Msk\msk_Z_lp38.png"

image_real= Image.open(image_real_path)
image_real = image_real.convert("RGB")
image_ref= Image.open(image_ref_path)
image_ref = image_ref.convert("RGB")
image_mask = Image.open(image_mask_path).convert("L")

defectDetection = DefectDetection()

# Create a window
cv2.namedWindow('Score_Threshold')
cv2.namedWindow('Area_Threshold')

# Create trackbars for controlling brightness, contrast, and gamma
cv2.createTrackbar('Score_Threshold', 'Score_Threshold', 50, 255, nothing)  # [0, 255]
cv2.createTrackbar('Area_Threshold', 'Area_Threshold', 50, 10000, nothing) 

prev_concat = []
detect_defect_mask = None
detect_dist_np_image = None

def detect(defect_color, concat_blocks, defect_score_th, defect_area_th):
    
    global prev_concat, detect_defect_mask, detect_dist_np_image

    binary_mask = np.array(image_mask) > 128
    binary_mask = (binary_mask * 255).astype(np.uint8)
    
    if concat_blocks != prev_concat:
        detect_defect_mask, detect_dist_np_image = defectDetection.detect(image_real, image_ref,concat_blocks=concat_blocks)
        prev_concat = concat_blocks

    defect_mask_crop = cv2.bitwise_and(detect_defect_mask,detect_defect_mask,mask=binary_mask)
    defect_mask_crop[defect_mask_crop < defect_score_th] = 0

    threshold_value = filters.threshold_otsu(defect_mask_crop)  # Otsu's method for automatic thresholding
    binary_image = defect_mask_crop > threshold_value
    labeled_image = measure.label(binary_image, connectivity=2)
    stats = measure.regionprops(labeled_image)

    labeled_image_color = color.label2rgb(labeled_image, bg_label=0, kind='overlay')
    labeled_image_color = (labeled_image_color * 255).astype(np.uint8)

    cv2_image = cv2.cvtColor(np.array(image_real), cv2.COLOR_RGB2BGR)
    kernel = np.ones((3, 3), np.uint8)

    for region in stats:  
        if region.area >= defect_area_th:
            mask = np.uint8(labeled_image == region.label)  # labels should be a 2D array with labels for each pixel

            dilated_image = cv2.dilate(mask, kernel, iterations=1)
            contours, _ = cv2.findContours(dilated_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(cv2_image, contours, -1, defect_color, 1)
        
    return detect_dist_np_image, labeled_image_color, cv2_image

prev_defect_score_th = -1
prev_defect_area_th = -1

while True:
    # Get the values from the trackbars
    defect_score_th = cv2.getTrackbarPos('Score_Threshold', 'Score_Threshold')
    defect_area_th = cv2.getTrackbarPos('Area_Threshold', 'Area_Threshold')

    if defect_score_th != prev_defect_score_th or defect_area_th != prev_defect_area_th:
            
        blue_color = (255, 0, 0)

        distance_np_image, labeled_image_color, cv2_image = detect(defect_color=blue_color, concat_blocks=[1,2,3], 
                                                                defect_score_th=defect_score_th, defect_area_th=defect_area_th)

        height, width = cv2_image.shape[:2]  # Get the dimensions of the first image

        distance_np_image = cv2.resize(distance_np_image, (width, height))
        distance_np_image = cv2.cvtColor(distance_np_image, cv2.COLOR_GRAY2BGR)

        stacked_images = cv2.hconcat([distance_np_image, cv2_image])

        aspect_ratio = stacked_images.shape[1] / stacked_images.shape[0]  # width / height
        new_height = int(width / aspect_ratio)  # Calculate new height based on aspect ratio
        stacked_images_resized = cv2.resize(stacked_images, (width, new_height))

        # Display the image
        cv2.imshow('Interactive Image', stacked_images_resized)

        prev_defect_score_th = defect_score_th
        prev_defect_area_th = defect_area_th

            # Exit the loop if 'ESC' key is pressed
    key = cv2.waitKey(1)
    if key == 27:  # ESC key to exit
        break
# Close all OpenCV windows
cv2.destroyAllWindows()
