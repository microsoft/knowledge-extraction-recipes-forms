#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import argparse
import os

import cv2
import matplotlib.pyplot as plt
import numpy as np


def bb_intersection_over_union(box_a, box_b):
    """
    Find out how much 2 boxes intersect
    :param box_a: 
    :param box_b: 
    :return: IOU overlap
    """
    # determine the (x, y)-coordinates of the intersection rectangle
    x_a = max(box_a[0], box_b[0])
    y_a = max(box_a[1], box_b[1])
    x_b = min(box_a[2], box_b[2])
    y_b = min(box_a[3], box_b[3])

    # compute the area of intersection rectangle
    intersect_area = max(0, x_b - x_a + 1) * max(0, y_b - y_a + 1)

    # compute the area of both the prediction and ground-truth
    # rectangles
    box_a_area = (box_a[2] - box_a[0] + 1) * (box_a[3] - box_a[1] + 1)
    box_b_area = (box_b[2] - box_b[0] + 1) * (box_b[3] - box_b[1] + 1)

    # compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area
    iou = intersect_area / float(box_a_area + box_b_area - intersect_area)

    # return the intersection over union value
    return iou


def find_forms_boundaries(input_image):
    grayscale_image = cv2.imread(input_image, cv2.IMREAD_GRAYSCALE)
    original_image = cv2.imread(input_image)
    threshold = 0.5
    _, threshold_image = cv2.threshold(grayscale_image, 200, 255, cv2.THRESH_BINARY_INV)

    document_height, document_width = grayscale_image.shape[0], grayscale_image.shape[1]
    contours, _ = cv2.findContours(threshold_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        approximated_polygon = cv2.approxPolyDP(contour, 0.1 * cv2.arcLength(contour, True), True)
        coordinates = approximated_polygon.ravel()

        # if quadrilateral
        if len(approximated_polygon) == 4:
            border_thickness = 0.1

            x, y, x2, y2 = coordinates[0], coordinates[1], coordinates[4], coordinates[5]
            feature_height, feature_width = (y2 - y), (x2 - x)

            # only use "significant" boxes
            if feature_width > float(document_width) * 0.1 and feature_height > float(document_height) * 0.1:
                cv2.drawContours(grayscale_image, [approximated_polygon], 0, 0, 5)
                return feature_width, feature_height

    return 0, 0


def find_checkboxes(input_image, template_folder):
    """
    locate the checked and empty checkboxes on a form (using template matching)
    :param input_image: the form
    :param template_folder: a template folder with image examples of checked and empty checkboxes
    :return: a copy of the form with the found checkboxes visually marked, a json string containing the type and location of each box
    """
    default_width = 1382

    form_width, form_height = find_forms_boundaries(input_image)
    scale = 1
    if form_width != 0:
        scale = default_width / form_width

    font = cv2.FONT_HERSHEY_TRIPLEX
    results = []
    img_rgb = cv2.imread(input_image)
    img_rgb = cv2.resize(img_rgb, (int(img_rgb.shape[1] * scale), int(img_rgb.shape[0] * scale)))
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

    for template_category in ["checked", "empty"]:
        for template_file in os.listdir(os.path.join(template_folder, template_category)):
            template = cv2.imread(os.path.join(template_folder, template_category, template_file), 0)
            template_width, template_height = template.shape[::-1]

            match_results = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
            threshold = 0.8
            location = np.where(match_results >= threshold)
            for point in zip(*location[::-1]):
                # Is it a duplicate (based on IOU)
                duplicate = False
                for result in results:
                    existing_check_box = result['boundingbox']
                    if bb_intersection_over_union(
                            [point[0], point[1], point[0] + template_width, point[1] + template_height],
                            existing_check_box) > 0.55:
                        duplicate = True
                        # print("duplicate found")

                if not duplicate:
                    results.append(
                        {"type": template_category,
                         "boundingbox": [point[0], point[1], point[0] + template_width, point[1] + template_height]})
                    cv2.rectangle(img_rgb, point, (point[0] + template_width, point[1] + template_height), (0, 0, 255),
                                  2)
                    cv2.putText(img_rgb, template_category, (point[0], point[1]), font, 0.5, 0)

    results = sorted(results, key=lambda checkbox: checkbox['boundingbox'][1])
    results = sorted(results, key=lambda checkbox: checkbox['boundingbox'][0])
    # add id
    for idx, result in enumerate(results):
        result['id'] = idx
    return img_rgb, results


def main():
    parser = argparse.ArgumentParser("find checkboxes in form")
    parser.add_argument('--form', type=str, required=True)
    parser.add_argument('--template_folder', type=str, default="templates")
    parser.add_argument('--output_image', type=str, default="result.jpg")
    args = parser.parse_args()

    result_image, results_json = find_checkboxes(args.form, args.template_folder)
    print(results_json)

    # Plot image and save to file.
    plt.imshow(result_image)
    cv2.imwrite(args.output_image, result_image)


if __name__ == "__main__":
    main()
