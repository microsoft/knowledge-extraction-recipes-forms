import argparse
import math

import cv2
import numpy as np
from matplotlib import pyplot as plt

debug = False


def plt_img(img):
    """
    Quick visualisation of the checked fields.
    :param img:
    :return:
    """
    if (debug):
        plt.figure(figsize=(30, 30))
        plt.imshow(img, 'gray')
        plt.show()


def im_threshold(img):
    """
    Thresholds values of light grey to white. Inverts colours to black page w/ white writing.
    :param img:
    :return:
    """
    # Thresholds light greys to white, and inverses the page to black.
    _, thresh = cv2.threshold(img, 200, 255, cv2.THRESH_BINARY_INV)
    # img = cv2.adaptiveThreshold(img,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,\
    #         cv2.THRESH_BINARY,11,2)
    return thresh


def bbox(contours):
    formbox = [999, 999, 0, 0]  # x1, y1, x2, y2
    for cnt in contours:
        minx = cnt[:, 0, 0].min()
        maxx = cnt[:, 0, 0].max()
        miny = cnt[:, 0, 1].min()
        maxy = cnt[:, 0, 1].max()
        if (minx < formbox[0]):
            formbox[0] = minx
        if (miny < formbox[1]):
            formbox[1] = miny
        if (maxx > formbox[2]):
            formbox[2] = maxx
        if (maxy > formbox[3]):
            formbox[3] = maxy
    return formbox


def analyze_form(img):
    """
    Returns the bounding box for the form and relative vectors 
    to checkboxes it finds. returns same image with
    :param img: loaded image file
    :return: bounding box based on opencv contours
    """
    # Get Contours
    thresholdimg = im_threshold(img)
    if cv2.getVersionMajor() in [2, 4]:
        contours, _ = cv2.findContours(
            thresholdimg, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    else:
        _, contours, _ = cv2.findContours(
            thresholdimg, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    formbox = bbox(contours)
    print(formbox)
    bbox_results = np.array([[[formbox[0], formbox[1]]], [[formbox[2], formbox[1]]], [[formbox[2], formbox[3]]],
                             [[formbox[0], formbox[3]]]])
    cv2.drawContours(img, bbox_results, 0, (0), 2)

    plt_img(img)
    return formbox


def get_vector(checkbox, formbox):
    # Get Center of checkbox
    x = checkbox[2] - checkbox[0]
    y = checkbox[3] - checkbox[1]
    # Return vector
    return [x - formbox[0], y - formbox[1]]


def check_find(img, thresholdimg, mark_thresh, check_type):
    """
    Returns an image labelled with all relevant checks, and a json with the details
    :param img:
    :param thresholdimg:
    :param mark_thresh:
    :param check_type:
    :return: image, results
    """
    if cv2.getVersionMajor() in [2, 4]:
        contours, _ = cv2.findContours(
            thresholdimg, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    else:
        _, contours, _ = cv2.findContours(
            thresholdimg, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    font = cv2.FONT_HERSHEY_TRIPLEX
    document_height, document_width = img.shape[0], img.shape[1]
    mark_thresh = float(mark_thresh.strip('%')) / 100.0

    results = []
    count = 0
    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, 0.1 * cv2.arcLength(cnt, True), True)
        coords = approx.ravel()

        # If quadrilateral
        if len(approx) == 4:
            border_thickness = 0.1
            sqaureness = 5  # (pixels)
            x, y, x2, y2 = coords[0], coords[1], coords[4], coords[5]
            feature_height, feature_width = (y2 - y), (x2 - x)
            # If the size of the quadrilateral found is significant (e.g. not hidden inside text)
            if feature_width > float(document_width) / 100 and feature_height > float(document_width) / 100:
                border_thickness_y = math.floor(border_thickness * feature_height)
                border_thickness_x = math.floor(border_thickness * feature_width)

                # If a square (± 5 pixels)
                if abs(feature_height - feature_width) < sqaureness:
                    # Is it a duplicate (based on IOU)
                    duplicate = False
                    for result in results:
                        existingCheckBox = result['boundingbox']
                        if (bb_intersection_over_union([x, y, x2, y2], existingCheckBox) > 0.55):
                            duplicate = True
                    if not duplicate:
                        checkbox = {}
                        checkbox['boundingbox'] = [x, y, x2, y2]
                        crop_img = img[y + border_thickness_y: y + feature_height - border_thickness_y,
                                   x + border_thickness_x: x + feature_width - border_thickness_x]
                        # Thresholds the image to binary black and white
                        _, crop_thresh = cv2.threshold(
                            crop_img, 127, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
                        total = crop_img.shape[0] * crop_img.shape[1]
                        count_black = total - cv2.countNonZero(crop_thresh)
                        if count_black > float(total) * mark_thresh and (
                                check_type == "checked" or check_type == "all"):
                            cv2.drawContours(img, [approx], 0, (0), 2)
                            cv2.putText(img, "Filled", (x, y), font, 1, (0))
                            checkbox['type'] = "checked"
                        elif check_type == "empty" or check_type == "all":
                            cv2.drawContours(img, [approx], 0, (0), 2)
                            cv2.putText(img, "Empty", (x, y), font, 0.5, (0))
                            checkbox['type'] = "empty"
                        results.append(checkbox)
        if len(approx) > 15:
            # TODO: Do something here if looking for radio buttons.
            continue
    results = sorted(results, key=lambda checkbox: checkbox['boundingbox'][1])
    results = sorted(results, key=lambda checkbox: checkbox['boundingbox'][0])
    for idx, result in enumerate(results):
        result['id'] = idx
    # add ID
    return img, results


def bb_intersection_over_union(boxA, boxB):
    # determine the (x, y)-coordinates of the intersection rectangle
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    # compute the area of intersection rectangle
    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)

    # compute the area of both the prediction and ground-truth
    # rectangles
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)

    # compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area
    iou = interArea / float(boxAArea + boxBArea - interArea)

    # return the intersection over union value
    return iou


def main():
    parser = argparse.ArgumentParser("find checkboxes in form")
    parser.add_argument('--form', type=str, required=True)
    parser.add_argument('--template_folder', type=str, default="templates")
    parser.add_argument('--output_image', type=str, default="result.jpg")
    args = parser.parse_args()

    check_type = 'all'
    fill_threshold = '30%'

    try:
        img = cv2.imread(args.form, cv2.IMREAD_GRAYSCALE)
    except cv2.error as e:
        print("Error reading image {}".format(args.form))
    mark_thresh = str(fill_threshold)
    threshold = im_threshold(img)
    img, results = check_find(img, threshold, mark_thresh, check_type)

    # Plot image and save to file.
    print(results)
    cv2.imwrite(args.output_image, img)


if __name__ == "__main__":
    main()
