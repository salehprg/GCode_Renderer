import cv2
import numpy as np
import torch
from defect_detection import DefectDetection
from my_resnet import ResnetModel
from PIL import Image
from skimage import measure, morphology, color

defect_detection = DefectDetection()

defect_score_th = 100
defect_area_th = 100

image_1= Image.open("Resnet/test_sq.jpg")
image_2= Image.open("Resnet/test_sq_2.jpg")

defect_mask, distance_np_image = defect_detection.detect(image_2, image_1,concat_blocks=[1])

cv2.imshow("Pixel-wise Euclidean Distance", distance_np_image)

image_2_np = cv2.cvtColor(np.array(image_2), cv2.COLOR_RGB2GRAY)
result_image = image_2_np * defect_mask
result_image[result_image < defect_score_th] = 0

result_image = np.clip(result_image, 0, 255)

labeled_image = measure.label(result_image, connectivity=2)
stats = measure.regionprops(labeled_image)

d1 = np.isin(labeled_image, [i + 1 for i, stat in enumerate(stats) if stat.area >= defect_area_th])

labeled_image = measure.label(d1, connectivity=2)
stats = measure.regionprops(labeled_image)

labeled_image_color = color.label2rgb(labeled_image, bg_label=0, kind='overlay')
labeled_image_color = (labeled_image_color * 255).astype(np.uint8)

cv2.imshow("Mask TH", labeled_image_color)
cv2.imshow("Mask result", result_image)

cv2.waitKey(0)
cv2.destroyAllWindows()