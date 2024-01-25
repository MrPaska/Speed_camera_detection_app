import os
import cv2
import easyocr
import numpy as np
from snackbar import alert_window
import re
from statistics import post_statistics

reader = easyocr.Reader(["en"])
zone_dict = dict()
i = 0
C = 2  # This is a constant that is subtracted from the average value of each block. Decreasing this value makes the image brighter, increasing it makes it darker.
block_size = 11  # A block size that specifies how many pixels around each pixel to use for averaging
pattern = re.compile(r"^\d{1,4}(m|km)$")  # digit by 1 to 9999 and m or km in the end


def process_img(saved_photos, user_id, image, zona_layout, video_play):
    for saved_photo in saved_photos:
        path = os.path.join("./", saved_photo)
        gray_img = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGRA2GRAY)
        read_text(gray_img)
        # Frame sharpening technic
        # Creating convolutional kernel a 3x3 matrix used as filter for frame
        # A factor of 9 in the center intensifies the central pixel, while surrounding factors of -1 decrease the brightness in the surrounding pixels.
        # The sharpening process increases the image contrast between pixels to make the image appear sharper
        # This method is effective for highlighting image details, especially useful if you want to increase clarity of texture or contours
        kernel = np.array([[-1, -1, -1],
                           [-1, 9, -1],
                           [-1, -1, -1]])
        sharpened_image = cv2.filter2D(image, -1, kernel) # 1 parameter specifies that the output image depth (number of bits per pixel ratio) will be the same as the original image
        read_text(sharpened_image)
        # This method is used for images where the lighting is not uniform throughout the image. Instead of a single threshold value for the entire image, adaptive thresholding uses different threshold values for different parts of the image.
        adaptive_mean_thresholding = cv2.adaptiveThreshold(gray_img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, block_size, C)
        read_text(adaptive_mean_thresholding)
        # A Gaussian filter assigns weights to the pixels around the pixel in question, meaning that closer pixels will have a greater effect on the threshold value than distant pixels. This allows for more efficient handling of local illumination changes in the image, enabling more accurate segmentation results.
        adaptive_gaussian_thresholding = cv2.adaptiveThreshold(gray_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block_size, 9)
        read_text(adaptive_gaussian_thresholding)
    max_value(user_id, image, zona_layout, video_play)


def read_text(image):
    global i
    i += 1
    try:
        results = reader.readtext(image)
        label = results[0][1]
        cleaned_label = ''.join(char for char in label if char.isalnum())
        label = cleaned_label.replace("l", "1").replace("I", "1")
        if pattern.match(label):
            conf = round(results[0][2], 2)
            zone_dict[i] = (label, conf)
    except Exception as e:
        print(e)


def max_value(user_id, image, zona_layout, video_play):
    global i
    max_val = 0
    if len(zone_dict) == 0:
        max_label = "nenuskaityta"
    else:
        for key, values in zone_dict.items():
            if max_val < values[1]:
                max_val = values[1]
                max_label = values[0]
    i = 0
    print(zone_dict)
    zone_dict.clear()
    print(f"Label: {max_label} max_value: {max_val}")
    if video_play is None:
        post_statistics("vidutinis", max_label, user_id, image)
    alert_window("Aptiktas vidutinio greičio matuoklis!", max_label, zona_layout, video_play)
