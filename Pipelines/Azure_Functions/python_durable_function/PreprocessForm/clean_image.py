import cv2

def clean(image):
    input_image = image

    # Do your OpenCV transformations here
    monochrome = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)


    output_image = monochrome

    return output_image
    