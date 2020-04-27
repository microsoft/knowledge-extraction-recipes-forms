import numpy as np
from matplotlib.patches import Polygon
import matplotlib.pyplot as plt
from PIL import Image, ImageStat, ImageOps
from io import BytesIO
import time
import logging

from common.request_helpers import get_request,post_request

def get_OCR_results(uri, post_headers, get_headers, image):

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
    x = int(box[0] + (box[4]-box[0])/2)
    y = int(box[1] + (box[5]-box[1])/2)
    center = {'x':x,'y':y}
    return center

def get_lines(data):
    lines = []
    for l in data['lines']:
        line = {}
        line['boundingBox'] = l['boundingBox']
        line['center'] = get_center(line['boundingBox'])
        line['text'] = l['text']
        lines.append(line)
    return lines

def grayscale_image(img):
    img = Image.open(img)
    img_grayscale = ImageOps.grayscale(img)
    img_grayscale_bytes = BytesIO()
    img_grayscale.save(img_grayscale_bytes, format='TIFF')
    image_data_grayscale = img_grayscale_bytes.getvalue()
    return image_data_grayscale

def get_form_data(image, subscription_key, region):

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
    img = Image.open(img)
    img_rotated = img.rotate(angle=angle, resample=Image.BICUBIC, expand=True)
    corrected_img = BytesIO()
    img_rotated.save(corrected_img, format='JPEG')
    return corrected_img

def blob_to_image(blob):
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

    
    
