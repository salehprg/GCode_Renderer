from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
import torch
import uvicorn
from Resnet import ResnetModel
from PIL import Image

model = ResnetModel()

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

parameters = {}
@app.post("/submit-form")
async def submit_form(data: FormData):
    global parameters
    print("Received Form Data:", data.dict())

    # Validate or process the data here as needed
    if not data.inputImagesFolder or not data.referenceImagesFolder or not data.maskImagesFolder:
        raise HTTPException(status_code=400, detail="All folder paths must be provided.")

    parameters = data.dict()
    return {
        "message": "Form data received successfully",
        "receivedData": data.dict()
    }

# Root endpoint for testing

@app.get("/test")
def test_image():
    image = Image.open("test_img.jpg")
    output = model(image)

    _, predicted_class = torch.max(output, 1)
    cls_name = model.get_class_name(predicted_class.item())
    print(f"Predicted class index: {cls_name}")
    
    return {"class": cls_name}

@app.get("/")
def read_root():
    return {"message": "API is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)