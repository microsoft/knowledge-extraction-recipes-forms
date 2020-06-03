import cv2
import numpy as np


def enhance_rectangles(image, kernels, plot=False):
	# new_image = np.zeros_like(image)
	# for kernel in kernels:
	# 	morphs = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel, iterations=1)
	# 	new_image += morphs
	# image = new_image

	new_image = np.zeros_like(image)
	for kernel in kernels:
		morphs = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel, iterations=1)
		new_image += morphs
	image = new_image
	image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY)[1]

	if plot:
		cv2.imshow("rectangular shape enhanced image", image)
		cv2.waitKey(0)
	
	return image


def enhance_image(image, kernels, plot=False):
	new_image = np.zeros_like(image)
	for kernel in kernels:
		morphs = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel, iterations=1)

		# kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,1))
		# morphs = cv2.dilate(morphs, kernel, iterations = 1)

		# kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1,3))
		# morphs = cv2.dilate(morphs, kernel, iterations = 1)

		morphs = cv2.morphologyEx(morphs, cv2.MORPH_OPEN, kernel, iterations=1)
		new_image += morphs
	image = new_image
	image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY)[1]

	if plot:
		cv2.imshow("enhanced image", image)
		cv2.waitKey(0)

	return image


def apply_thresholding(image, plot=False):
	otsu  = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
	binary = cv2.threshold(image, np.mean(image) , 255, cv2.THRESH_BINARY_INV)[1]
	image = otsu + binary
	# image = cv2.threshold(image, np.median(image), 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]

	# image = cv2.adaptiveThreshold(image,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,\
	#             cv2.THRESH_BINARY_INV,5,3)
	# image = cv2.adaptiveThreshold(image,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,\
	#             cv2.THRESH_BINARY_INV,3,5)
	if plot:
		cv2.imshow("thresholded image", image)
		cv2.waitKey(0)
	return image


def get_rect_kernels(
		wh_ratio_range=(0.5, 1.1),
		min_w=40,
		max_w=60,
		min_h=40,
		max_h=65,
		pad=1
	):

	kernels = [
		np.pad(np.zeros((h,w), dtype=np.uint8), pad, constant_values=1, mode='constant')
		for w in range(min_w, max_w)
		for h in range(min_h, max_h)
		if w/h >= wh_ratio_range[0] and w/h <= wh_ratio_range[1]
	]

	return kernels


def get_line_kernels(length):
    kernels = [
		np.ones((length, 2), dtype=np.uint8),
		np.ones((2, length), dtype=np.uint8),
		# np.pad(np.ones((3,2), dtype=np.uint8), ((0,0),(1,0)), constant_values=0),
		# np.pad(np.ones((3,2), dtype=np.uint8), ((0,0),(0,1)), constant_values=0),
		# np.pad(np.ones((2,3), dtype=np.uint8), ((1,0),(0,0)), constant_values=0),
		# np.pad(np.ones((2,3), dtype=np.uint8), ((0,1),(0,0)), constant_values=0),
    ]
    return kernels


def draw_rects(image, rects, color=(0, 255, 0), thickness=1):
	# loop over the contours
	for r in rects:
		x, y, w, h = r
		cv2.rectangle(image, (x, y), (x+w, y+h), color, thickness)
	return image
