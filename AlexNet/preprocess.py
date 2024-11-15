from torchvision import transforms
class PreProcess:
    def __init__(self):
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        pass

    def preprocess(self, image):
        input_tensor = self.transform(image).unsqueeze(0)
        return input_tensor