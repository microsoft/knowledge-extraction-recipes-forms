import cv2
import numpy as np
import imutils


def group_countours(cnts):
	rects = [get_bounding_rect(c)[:4] for c in cnts]
	# we need to duplicate all the rects for grouping below to work
	rects += rects
	rects, weights = cv2.groupRectangles(rects, 1, 0.2)
	return rects


def get_bounding_rect(c):
	peri = cv2.arcLength(c, True)
	approx = cv2.approxPolyDP(c, 3, True)
	(x, y, w, h) = cv2.boundingRect(approx)
	if len(approx) == 4:
		return x, y, w, h, True
	return x, y, w, h, False


def check_rect_ratio(c, wh_ratio_range):
	(x, y, w, h, is_rect) = get_bounding_rect(c)
	ar = w / float(h)
	if is_rect and ar >= wh_ratio_range[0] and ar <= wh_ratio_range[1]:
		return True
	return False


def filter_contours_by_rect_ratio(cnts, wh_ratio_range):
	return [
		c for c in cnts
		if check_rect_ratio(c, wh_ratio_range)
	]


def get_contours(image):
	# find contours in the thresholded image
	cnts = cv2.findContours(
		image.copy(),
		cv2.RETR_LIST,
		cv2.CHAIN_APPROX_SIMPLE
	)
	cnts = imutils.grab_contours(cnts)
	return cnts


def filter_contours_by_area_size(cnts, area_range):
	cnts_filtered = []
	for c in cnts:
		area = cv2.contourArea(c)
		if area > area_range[0] and area < area_range[1]:
			cnts_filtered.append(c)
	return cnts_filtered


def rescale_contours(cnts, ratio):
	cnts_rescaled = []
	for c in cnts:
		c = c.astype("float")
		c *= ratio
		c = c.astype("int")
		cnts_rescaled.append(c)
	return cnts_rescaled


def get_grouping_rectangles(rect_groups):
    rectangles = []
    for group in rect_groups:
        points = []
        for rect in group:
            points.append((rect[0], rect[1]))
            points.append((rect[0] + rect[2], rect[1] + rect[3]))
        rectangles.append(cv2.boundingRect(np.asarray(points)))
    return rectangles


def get_groups_from_groups(
		rects,
		max_distance,
		min_group_size,
		grouping_mode='vertical'):
	rect_groups = [
		rect_group
		for rect_group in(
			group_rects(
				np.asarray(group), max_distance=max_distance,
				min_group_size=min_group_size, grouping_mode=grouping_mode)
			for group in rects)
		if rect_group != []
	]
	rect_groups = [
		horizontal_group
		for vertical_group in rect_groups
		for horizontal_group in vertical_group
	]
	return rect_groups


def group_rects(rects, max_distance,  min_group_size=1, grouping_mode='vertical'):
	grouping_mode = grouping_mode.lower()
	assert(grouping_mode in ['vertical', 'horizontal'])
	if grouping_mode == 'vertical':
		m, n = (1, 3)
	elif grouping_mode == 'horizontal':
		m, n = (0, 2)

	rects_sorted = rects[np.argsort(rects[:, m])]
	new_groups = []
	temp_group = []
	temp_group.append(rects_sorted[0])
	for i in range(1, len(rects_sorted)):
		rect1 = rects_sorted[i-1]
		x1 = rect1[m] + int(rect1[n] / 2)

		rect2 = rects_sorted[i]
		x2 = rect2[m] + int(rect1[n] / 2)

		distance = abs(x2 - x1)
		if distance <= max_distance:
		    temp_group.append(rect2)
		else:
		    new_groups.append(temp_group)
		    temp_group = []
		    temp_group.append(rect2)

		if i == len(rects_sorted) - 1:
			new_groups.append(temp_group)
	new_groups = [group for group in new_groups if len(group) >= min_group_size]
	return new_groups
