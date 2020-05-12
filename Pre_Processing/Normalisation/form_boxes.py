# Module with routines for preparing forms with individual character boxes for recognition using Form Recognizer.
#
# Main methods:
# * preprocessForm(original_form_image)
# * cleanAndDetectFields(preprocessed_form_image)
# * cleanAndOutlineFields(preprocessed_form_image)
#
# All input and output images are in OpenCV format.
# Recommended input: scanned grayscale, non-processed TIF, 300dpi.

import cv2
import numpy as np
import os
import argparse
import glob
import math
import imutils
import requests
import time


# Width of the normalized image.
NORMALIZED_IMAGE_WIDTH = 2480

# Minimum box perimeter in pixels.
MIN_BOX_SIZE = 240

# Maximum box perimeter in pixels.
MAX_BOX_SIZE = 320


# Gets form box information with normalized angle (between -45..45).
def getFormBoxInfo(box):
    angle = box[2]
    width, height = box[1]
    while -45 > angle:
        angle += 90
        temp = width
        width = height
        height = temp

    while 45 < angle:
        angle -= 90
        temp = width
        width = height
        height = temp

    return (box[0], (width, height), angle)
    

# Gets an average angle of boxes for form alignment.
def getBoxesAngleForFormAlignment(boxes):
    avg_angle = 0

    for box in boxes:
        _, __, a = getFormBoxInfo(box)
        avg_angle += a

    return avg_angle / len(boxes)


# Detects all boxes in the form.
def getFormBoxes(grayscale):
    element = cv2.getStructuringElement(cv2.MORPH_CROSS,(5,5))
    dilated = cv2.dilate(grayscale,element)
    _,thresholded = cv2.threshold(dilated,150,255,cv2.THRESH_BINARY_INV)    
    contours,_ = cv2.findContours(thresholded,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    boxes = []

    for contour in contours:
        convex = cv2.convexHull(contour)
        perimeter = cv2.arcLength(convex, True)
        approx_contour = cv2.approxPolyDP(convex, perimeter * 0.1, True)
        if len(approx_contour) == 4:
            box_rect = cv2.minAreaRect(approx_contour)
            box_size = int(perimeter)

            if MIN_BOX_SIZE < box_size < MAX_BOX_SIZE:
                boxes.append(box_rect)

    return boxes


# Pre-processes form by converting it to grayscale and aligns it vertically.
# Returns: the pre-processed form. 
def preprocessForm(original_form):
    
    # STEP 1: Resize.
    source_height = original_form.shape[0]
    source_width = original_form.shape[1]

    target_width = NORMALIZED_IMAGE_WIDTH
    target_height = int(source_height * target_width / source_width)
    
    resized_form = cv2.resize(original_form, (target_width, target_height), interpolation = cv2.INTER_AREA)
    
    # STEP 2: Convert to grayscale.
    grayscale_form = cv2.cvtColor(resized_form, cv2.COLOR_BGR2GRAY)

    # STEP 3: Align form vertically using an average angle of the character boxes.
    boxes = getFormBoxes(grayscale_form)
    angle = getBoxesAngleForFormAlignment(boxes)
    aligned_form = cv2.bitwise_not(imutils.rotate(cv2.bitwise_not(grayscale_form), angle))

    return aligned_form


# Detects rows of boxes.
# Returns: array of rows of boxes.
def getRowsOfBoxes(boxes):
    rows = []
    remaining_boxes = boxes

    while len(remaining_boxes) > 0:
        non_row_boxes = []
        row = []
        first_box = remaining_boxes[0]
        row_height = first_box[1][1]
        row_y = first_box[0][1]
        for box in remaining_boxes:
            box_y = box[0][1]
            if -row_height / 2 < box_y - row_y < row_height / 2:
                row.append(box)
            else:
                non_row_boxes.append(box)
        
        row_top = row_y
        row_bottom = row_y

        for box in row:
            box_y = box[0][1]
            box_height = box[1][1]
            box_top = box_y - box_height / 2
            box_bottom = box_y + box_height / 2
            if row_top > box_top:
                row_top = box_top
            if row_bottom < box_bottom:
                row_bottom = box_bottom 

        rows.append({ 'top': row_top, 'bottom': row_bottom, 'boxes': row })
        remaining_boxes = non_row_boxes
    
    return rows


# Removes box frames.
# Returns: image without box frames.
# NOTE: This implementation modifies the input image.
def removeBoxFrames(form, boxes):
    for box in boxes:
        box_contour = np.int0(cv2.boxPoints(box))
        cv2.drawContours(form, [box_contour], 0, (255, 255, 255), 18)

    return form


# Cleans form background and adjusts it for better handwriting recogntiion.
# Returns: form image with clean white background.
def cleanFormBackground(form):
    element = cv2.getStructuringElement(cv2.MORPH_CROSS,(3,3))
    eroded = cv2.erode(form, element)
    inverted = cv2.bitwise_not(eroded)
    _,filtered_inverted = cv2.threshold(inverted, 50, 255, cv2.THRESH_TOZERO)
    filtered = cv2.bitwise_not(filtered_inverted)

    return filtered


# Gets fields from the row of boxes by detecting continuous runs of boxes.
# Returns: array of fields in the following form: { 'left': <float>, 'right': <float>, 'top': <float>, 'bottom': <float>, 'boxes': ... }.
def getFieldsFromRow(row):
    fields = []
    remaining_boxes = sorted(row['boxes'], key=lambda box: box[0][0], reverse=False)

    while (len(remaining_boxes) > 0):
        field_boxes = []
        non_field_boxes = []
        first_box = remaining_boxes[0]
        field_x = first_box[0][0]
        field_left = field_x
        field_right = field_x
        
        for box in remaining_boxes:
            box_x = box[0][0]
            box_width = box[1][0]
            box_left = box_x - box_width / 2
            box_right = box_x + box_width / 2
            if -box_width * 1.5 < box_x - field_x < box_width * 1.5:
                field_boxes.append(box)
                field_x = box_x
                if field_left > box_left:
                    field_left = box_left
                if field_right < box_right:
                    field_right = box_right
            else:
                non_field_boxes.append(box)
        
        fields.append({
            'left': field_left,
            'right': field_right,
            'top': row['top'],
            'bottom': row['bottom'],
            'boxes': field_boxes
            })

        remaining_boxes = non_field_boxes

    return fields


# Cleans form, remove box borders and detects field boundaries. The form must be pre-processed using preprocessForm method.
# Returns: (clean_form, fields) where
# * clean_form - is form image with clean background and without box frames,
# * fields - array of detected fields in the same format as they are returned from getFieldsFromRow method.
def cleanAndDetectFields(form):
    
    # STEP 1: Detecting all boxes in the form.
    boxes = getFormBoxes(form)

    # STEP 2: Removing box borders.
    removeBoxFrames(form, boxes)

    # STEP 3: Cleaning background.
    clean_form = cleanFormBackground(form)
    
    # STEP 4: Detecting rows of boxes.
    rows = getRowsOfBoxes(boxes)

    # STEP 5: Detecting continuous runs of boxes within rows and adding borders around them.
    fields = []

    for row in rows:
        row_fields = getFieldsFromRow(row)

        for field in row_fields:
            fields.append(field)

    return (clean_form, fields)


# Adds borders around fields detected in the form. The form must be pre-processed using preprocessForm method.
# Returns: form image with clean background, without character box frames, but with field outlines.
def cleanAndOutlineFields(form):
    
    (clean_form, fields) = cleanAndDetectFields(form)

    for field in fields:
        top = int(field['top'])
        bottom = int(field['bottom'])
        left = int(field['left'])
        right = int(field['right'])
        cv2.rectangle(clean_form, (left, top), (right, bottom), (0, 128, 0), 2)        

    return clean_form


# Processes single form file (input_path) and stores result as output_path.
def processForm(input_path, output_path):
    input_form = cv2.imread(input_path)
    preprocessed_form = preprocessForm(input_form)
    output_form = cleanAndOutlineFields(preprocessed_form)

    cv2.imwrite(output_path, output_form)


# Processes forms from the input_dir and stores results in the output_dir.
# Example: processForms('src/', 'dst/')
def processForms(input_dir, output_dir):
    input_files = glob.glob(input_dir + '*.*')
    for input_path in input_files:
        extension = input_path.split('.')[-1] 
        filename = input_path.split('\\')[-1][:-len(extension)]
        output_path = output_dir + filename + extension
        processForm(input_path, output_path)