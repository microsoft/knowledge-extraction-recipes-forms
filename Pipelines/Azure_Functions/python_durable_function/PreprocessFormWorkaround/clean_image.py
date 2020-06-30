import logging
import io
import numpy as np
import math
import imutils
import cv2
import os

def clean(image):
    input_image = image

    # Do your OpenCV transformations here
    monochrome = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)

    output_image = monochrome

    return output_image
    