import cv2
import os
from natsort import natsorted

# Specify the folder containing the images and the output video file
image_folder = 'images_20241010-011130'  # Replace with your folder path
output_video = f'video_{image_folder}.mp4'  # Name of the output video file

# Get a sorted list of all the image files in the folder
images = [img for img in os.listdir(image_folder) if img.endswith(('.png', '.jpg', '.jpeg'))]
images = natsorted(images)  # Sort images in natural order

# Read the first image to get the frame size
frame = cv2.imread(os.path.join(image_folder, images[0]))
height, width, layers = frame.shape
frame_size = (width, height)

# Define the codec and create the VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # For MP4 format
video = cv2.VideoWriter(output_video, fourcc, 30, frame_size)  # 30 is the frame rate

# Loop through the images and write them to the video
for image in images:
    img_path = os.path.join(image_folder, image)
    frame = cv2.imread(img_path)
    video.write(frame)

# Release the video writer object
video.release()

print("Video has been created successfully!")