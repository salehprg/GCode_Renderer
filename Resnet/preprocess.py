from torchvision import transforms

# Define a transform to preprocess the image with the new size



class PreProcess:
    def __init__(self):
        self.transform = transforms.Compose([
            transforms.Resize((720, 1280)),  # Resize to 1280x720
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        pass

    def preprocess(self, image):
        input_tensor = self.transform(image).unsqueeze(0)
        return input_tensor