import cv2
import imutils
import numpy as np

from boxdetect.rect_proc import (
    filter_contours_by_area_size,
    filter_contours_by_rect_ratio,
    get_bounding_rect, get_contours,
    get_grouping_rectangles,
    get_groups_from_groups,
    group_countours, group_rects, rescale_contours)
from boxdetect.img_proc import (
    apply_thresholding, draw_rects,
    get_line_kernels, get_rect_kernels,
    enhance_image, enhance_rectangles)


def process_image(img, config, plot=False):
    assert(type(img) in [np.ndarray, str])
    if type(img) is np.ndarray:
        image_org = img.copy()
    elif type(img) is str:
        print("Processing file: ", img)
        image_org = cv2.imread(img)

	# parameters
    min_w, max_w = (config.min_w, config.max_w)
    min_h, max_h = (config.min_h, config.max_h)
    wh_ratio_range = config.wh_ratio_range
    padding = config.padding
    thickness = config.thickness
    scaling_factors = config.scaling_factors

    dilation_kernel = config.dilation_kernel
    dilation_iterations = config.dilation_iterations

    min_group_size = config.min_group_size 
    vertical_max_distance = config.vertical_max_distance
    horizontal_max_distance_multiplier = config.horizontal_max_distance_multiplier

    # process image using range of scaling factors
    cnts_list = []
    for scaling_factor in scaling_factors:
    	# resize the image for processing time
    	image = image_org.copy()
    	image = imutils.resize(image, width=int(image.shape[0] * scaling_factor))

    	resize_ratio = image_org.shape[0] / image.shape[0]
    	resize_ratio_inv =image.shape[0] / image_org.shape[0]

    	min_w_res = int(min_w * resize_ratio_inv)
    	max_w_res = int(max_w * resize_ratio_inv)
    	min_h_res = int(min_h * resize_ratio_inv)
    	max_h_res = int(max_h * resize_ratio_inv)

    	area_range = (
    		round(min_w_res * min_h_res * 0.90),
    		round(max_w_res * max_h_res * 1.00)
    	)		    
    	# convert the resized image to grayscale
    	image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    	# apply tresholding to get all the pixel values to either 0 or 255
    	# this function also inverts colors (black pixels will become the background)
    	image = apply_thresholding(image, plot) 

    	# basic pixel inflation
    	kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, dilation_kernel)
    	image = cv2.dilate(
            image, kernel, iterations=dilation_iterations)
    	if plot:
    		cv2.imshow("dilated", image)
    		cv2.waitKey(0)

    	# creating line-shape kernels to be used for image enhancing step
    	# try it out only in case of very poor results with previous setup
    	# kernels = get_line_kernels(length=4)
    	# image = enhance_image(image, kernels, plot)

    	# creating rectangular-shape kernels to be used for extracting rectangular shapes		
    	kernels = get_rect_kernels(
    		wh_ratio_range = wh_ratio_range,
    		min_w = min_w_res,	max_w = max_w_res,
    		min_h = min_h_res,	max_h = max_h_res,
    		pad=padding)
    	image = enhance_rectangles(
            image, kernels, plot)    

    	# find contours in the thresholded image
    	cnts = get_contours(image)
        # filter countours based on area size
    	cnts = filter_contours_by_area_size(cnts, area_range)
        # rescale countours to original image size
    	cnts = rescale_contours(cnts, resize_ratio)
        # add countours detected with current scaling factor run to the global collection
    	cnts_list += cnts
    # filter gloal countours by rectangle WxH ratio
    cnts_list = filter_contours_by_rect_ratio(cnts_list, wh_ratio_range)
    # merge rectangles into group if overlapping
    rects = group_countours(cnts_list)
    mean_width = np.mean(rects[:,2])
    mean_height = np.mean(rects[:,3])
    # group rectangles vertically (line by line)
    vertical_rect_groups = group_rects(
        rects, max_distance=vertical_max_distance,
        min_group_size=min_group_size, grouping_mode='vertical')
    # group rectangles horizontally (horizontally cluster nearby rects)
    rect_groups = get_groups_from_groups(
        vertical_rect_groups, max_distance=mean_width * horizontal_max_distance_multiplier,
        min_group_size=min_group_size, grouping_mode='horizontal')
    # get grouping rectangles
    grouping_rectangles = get_grouping_rectangles(rect_groups)

    # draw character rectangles on original image
    image_org = draw_rects(
        image_org, rects, color=(0, 255, 0), thickness=thickness)
    # draw grouping rectangles on original image
    image_org = draw_rects(
        image_org, grouping_rectangles, color=(0, 0, 255), thickness=thickness)

    if plot:
    	cv2.imshow("Org image with boxes", image_org)
    	cv2.waitKey(0)

    return rects, grouping_rectangles, img, image_org
