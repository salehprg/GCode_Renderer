import json
import torch.nn as nn
import torchvision.models as models
from preprocess import PreProcess

class ResnetModel(nn.Module):
    def __init__(self):
        super(ResnetModel, self).__init__()
        self.model = models.resnet50(pretrained=True)
        self.model.eval()
        self.preprocess = PreProcess()

        with open('class_names.json') as f:
            self.class_labels = json.load(f)
        pass

    def forward(self, x):
        input_tensor = self.preprocess.preprocess(x)
        return self.model(input_tensor)
    
    def get_class_name(self, index):
        return self.class_labels[f"{index}"][1]