#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
This script comprises of helper methods that provide utilities to
    - request Azure Cognitive Services OCR text extraction using "asyncBatchAnalyze" service
    - parse the Azure Cognitive Services OCR extraction results
    - compute the centeroid (center point) of a bounding box
    - convert an image to grayscale
    - rotate and image
    - convert an image file to byte array
"""
import numpy as np
from matplotlib.patches import Polygon
import matplotlib.pyplot as plt
from PIL import Image, ImageStat, ImageOps
from io import BytesIO
import time
import logging

from common.request_helpers import get_request,post_request


def get_OCR_results(uri, post_headers, get_headers, image):
    """
    Get OCR analysis results from Azure Cognitive Services OCR text extraction.

    Arguments:
        uri (str): URI to request the text extraction results
        post_headers (Dict): request headers comprising of "Content-Type" and "Ocp-Apim-Subscription-Key"
        get_headers (Dict): request header comprising of "Ocp-Apim-Subscription-Key"
        image (Image): Byte array image to be processed

    Return:
        operation_result (JSON): JSON response message detailing the results of OCR request
    """
    response = post_request(uri, image, post_headers)

    if(response != None):
        if(response.status_code == 202):
            operation_location = response.headers['Operation-Location']
            status = 'Running'
            while(status == 'Running'):
                operation_result = get_request(operation_location, get_headers)
                status = operation_result['status']
                logging.info("OCR operation status: %s"%status)
                time.sleep(1)

        return operation_result

    else:

        logging.error("Could not get OCR results.")
        return None

def get_center(box):
    """
    Get bounding box centeroid.

    Arguments:
        box (list): List of bounding box coordinates returned from Azure Cognitive Services API.
                    The list would comprise of x-coordinate, y-coordinate from the left-top corner of the image.

    Return:
        center (Dict): x and y coordinates of the centeroid
    """
    x = int(box[0] + (box[4]-box[0])/2)
    y = int(box[1] + (box[5]-box[1])/2)
    center = {'x':x,'y':y}
    return center

def get_lines(data):
    """
    Extract the horizontal lines the Azure Cognitive Services API recognized.

    Arguments:
        data (Dict): The dictionary comprising of the Azure Cognitive Services recognition results.

    Return:
        lines (List): A Dictionary list of "boundingBox" coordinates, "centeroid" coordinates and "text" extracted
    """
    lines = []
    for l in data['lines']:
        line = {}
        line['boundingBox'] = l['boundingBox']
        line['center'] = get_center(line['boundingBox'])
        line['text'] = l['text']
        lines.append(line)
    return lines

def grayscale_image(img):
    """
    Convert an image to grayscale

    Arguments:
        img (str): Path to image

    Return:
        image_data_grayscale (bytes): Grayscaled Byte array image
    """
    img = Image.open(img)
    img_grayscale = ImageOps.grayscale(img)
    img_grayscale_bytes = BytesIO()
    img_grayscale.save(img_grayscale_bytes, format='TIFF')
    image_data_grayscale = img_grayscale_bytes.getvalue()
    return image_data_grayscale

def get_form_data(image, subscription_key, region):
    """
    This method requests Azure Cognitive Services "asyncBatchAnalyze" service for text extraction.
    The method uses grayscale_image, get_OCR_results and get_lines methods

    Arguments:
        image (str): Path to image
        subscription_key (str): Azure Subscription key for the Azure Cognitive Service
        region (str): The Azure region the subscription resides
    Raises:
        Exception: When there is an error during request and extracting recognition results.
    Return:
        form_data (Dict): Dictionary that comprises of image "orientation", "width", "height" metadata. Dictionary also cointains the extracted "lines"
    """
    form_data = None

    try:
        URI = "https://{}.api.cognitive.microsoft.com/vision/v2.0/read/core/asyncBatchAnalyze".format(region)
        POST_HEADERS = {
        'Content-Type': 'application/octet-stream',
        'Ocp-Apim-Subscription-Key': subscription_key
        }
        GET_HEADERS = {
        'Ocp-Apim-Subscription-Key': subscription_key
        }

        image_grayscale = grayscale_image(image)
        OCR_results = get_OCR_results(URI, POST_HEADERS, GET_HEADERS, image_grayscale)

        if(OCR_results != None):
           data = OCR_results['recognitionResults'][0]

           form_data = {}
           form_data['orientation'] = data['clockwiseOrientation']
           form_data['width'] = data['width']
           form_data['height'] = data['height']
           form_data['lines'] = get_lines(data)

           logging.info("Form data retrieved successfully.")

        else:
           logging.error("Could not retrieve form data.")

    except Exception as e:
        logging.error("Error getting form data: %s"%e)

    return form_data

def rotate_image(img, angle, width, height):
    """
    Rotate an image based on current orientation angle.

    Arguments:
        img (str): Path to image
        angle (int): orientation angle detected during Azure Cognitive Services text extraction
        width (int): width of image detected during Azure Cognitive Services text extraction
        height (int): height of image detected during Azure Cognitive Services text extraction

    Return:
        corrected_img (bytes): Rotated Byte array image
    """
    img = Image.open(img)
    img_rotated = img.rotate(angle=angle, resample=Image.BICUBIC, expand=True)
    corrected_img = BytesIO()
    img_rotated.save(corrected_img, format='JPEG')
    return corrected_img

def blob_to_image(blob):
    """
    Convert an image hosted in a Azure Blob Container to a Byte Array Image

    Arguments:
        blob (azure.storage.blob.models.Blob): Azure Blob object to be converted to Byte Array Image

    Return:
        img (bytes): Converted Byte array image
    """
    if(blob != None):
        try:
            image_bytes = blob.content
            img = BytesIO(image_bytes)
            logging.info("Blob %s converted to image object."%blob.name)
            return img
        except Exception as e:
            logging.error("Could not convert blob %s to image object: %s"%(blob.name,e))
            return None
    return None