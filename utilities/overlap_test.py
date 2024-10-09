import cv2
import numpy as np

# Load the two images
image1 = cv2.imread('images_20241003-011737\layer_24.png')
image2 = cv2.imread('images\img_2024-08-23T20-01-53.687Z_lp22.jpg')

size = (1280,720)

# Resize the images if they are not of the same size
image1 = cv2.resize(image1, size)
image2 = cv2.resize(image2, size)

# Blend the images using weighted sum (alpha blending)
alpha = 0.5
beta = 1 - alpha
blended_image = cv2.addWeighted(image1, alpha, image2, beta, 0)

# Alternatively, compute the difference between the two images
difference = cv2.absdiff(image1, image2)

# Show the images
cv2.imshow('Blended Image', blended_image)
cv2.imshow('Difference', difference)

cv2.waitKey(0)
cv2.destroyAllWindows()
