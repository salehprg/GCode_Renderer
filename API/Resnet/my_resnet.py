import json
import os
from pathlib import Path
import numpy as np
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
from preprocess import PreProcess

class ResnetModel(nn.Module):
    def __init__(self):
        super(ResnetModel, self).__init__()
        model = models.resnet18(pretrained=True)
        model.eval()
        self.preprocess = PreProcess()

        block1  = nn.Sequential(
                            model.conv1,
                            model.bn1,
                            model.relu,
                            model.maxpool,
                            model.layer1  # ResNet Block 1
                        )
        block2 = model.layer2
        block3 = model.layer3
        
        for param in block1.parameters():
            param.requires_grad = False

        for param in block2.parameters():
            param.requires_grad = False

        for param in block3.parameters():
            param.requires_grad = False

        self.model = model
        self.block1 = block1
        self.block2 = block2
        self.block3 = block3

        path = Path(__file__)
        with open(os.path.join(path.parent,'class_names.json')) as f:
            self.class_labels = json.load(f)
        pass

    def block1_out(self,input):
        return self.block1(input)
    
    def block2_out(self,output_block1):
        output_block2 = self.block2(output_block1)
        output_block2 = F.interpolate(output_block2, size=(180, 320), mode='nearest')

        return output_block2
    
    def block3_out(self,output_block2):
        output_block3 = self.block3(output_block2)
        output_block3 = F.interpolate(output_block3, size=(180, 320), mode='nearest')

        return output_block3
    
    def tensor_to_image(self, tensor):
        result = tensor[0, 0, :, :].detach().cpu().numpy()
        result = (result - result.min()) / (result.max() - result.min()) * 255
        return result.astype(np.uint8)

    def forward(self, x):
        input_tensor = self.preprocess.preprocess(x)
        return self.model(input_tensor)
    
    def get_class_name(self, index):
        return self.class_labels[f"{index}"][1]