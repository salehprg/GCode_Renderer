import json
import torch
import torch.nn as nn
import torchvision.models as models
from alexnet import AlexNetModel
from preprocess import PreProcess
from PIL import Image

model = AlexNetModel()

image = Image.open("test_img.jpg")
output = model(image)

_, predicted_class = torch.max(output, 1)
cls_name = predicted_class.item()
print(f"Predicted class index: {cls_name}")

input_tensor = model.preprocess.preprocess(image)
output_block1 = model.block1(input_tensor)
print("Output after Block 1:", output_block1.shape)

# Pass the output to Block 2
output_block2 = model.block2(output_block1)
print("Output after Block 2:", output_block2.shape)

# Pass to Block 3
output_block3 = model.block3(output_block2)
print("Output after Block 3:", output_block3.shape)
