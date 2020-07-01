# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import cv2

def clean(image):
    input_image = image

    # Add your OpenCV transformations here, for example the removal of boxes
    # https://github.com/microsoft/knowledge-extraction-recipes-forms/blob/master/Demos/RemoveBoxes.ipynb
    monochrome = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)


    output_image = monochrome

    return output_image
    