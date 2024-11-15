import cv2
import os
from natsort import natsorted

def create_video(image_folder,prefix):

    if not os.path.exists("./videos"):
        os.mkdir("./videos")
    
    output_video = f'./videos/video_{prefix}_{image_folder}.mp4' 

    images = [img for img in os.listdir(image_folder) if img.endswith(('.png', '.jpg', '.jpeg')) and img.startswith(prefix)]
    images = natsorted(images)  # Sort images in natural order

    frame = cv2.imread(os.path.join(image_folder, images[0]))
    height, width, layers = frame.shape
    frame_size = (width, height)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # For MP4 format
    video = cv2.VideoWriter(output_video, fourcc, 30, frame_size)  # 30 is the frame rate

    for image in images:
        img_path = os.path.join(image_folder, image)
        frame = cv2.imread(img_path)
        video.write(frame)

    video.release()


image_folder = 'images_20241104-230453'
create_video(image_folder,"bed")
print("Bed Video has been created successfully!")
create_video(image_folder,"msk")
print("Mask Video has been created successfully!")
create_video(image_folder,"sim")
print("Sim Video has been created successfully!")