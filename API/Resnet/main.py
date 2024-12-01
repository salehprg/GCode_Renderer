import torch
from my_resnet import ResnetModel
from PIL import Image


model = ResnetModel()

image = Image.open("test_img.jpg")
output = model(image)

_, predicted_class = torch.max(output, 1)
cls_name = model.get_class_name(predicted_class.item())
print(f"Predicted class index: {cls_name}")
