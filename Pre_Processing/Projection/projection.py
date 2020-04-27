import cv2
import numpy as np
import sys


def find_runs(sum_rows, level=0):
    """
    Identify sequence of rows where the sum is high.
    This indicates existence of text (where the sum is above level)
    Do the same for sequences where the sum is low
    This indicates a line break - the abscence of text
    """
    lows = []
    highs = []
    num_rows = len(sum_rows)
    old_low_high = -1
    curr_run = []

    for pos in range(num_rows):

        if sum_rows[pos] <= level:
            low_high = 0
        else:
            low_high = 1

        if old_low_high == -1:
            old_low_high = low_high
            curr_run.append(pos)
            continue

        if old_low_high != low_high:
            # new run
            if old_low_high == 0:
                lows.append(curr_run)
            else:
                highs.append(curr_run)

            old_low_high = low_high
            curr_run = []

        curr_run.append(pos)

    return lows, highs


def analyze_runs(lows):

    print("lows")
    lmr_low = []
    for run in lows:
        middle_of_run = ((run[-1] - run[0])/2) + run[0]
        run_width = run[-1] - run[0]
        lmr_low.append([run[0], middle_of_run, run[-1], run_width])

        print(f"num points: {len(run)}"
              f" run_width: {run_width}"
              f" middle pos of run: {middle_of_run}")

    # extract details of each 'low' - start, middle, end, width
    widths = []
    num_seqs = len(lmr_low)
    prev_lmr = None
    for i in range(num_seqs):
        lmr = lmr_low[i]
        if prev_lmr is None:
            prev_lmr = lmr_low[i]
            continue

        pl, pm, pr, pw = prev_lmr
        l, m, r, w = lmr

        widths.append(m-pm)
        prev_lmr = lmr

    median_width = np.median(widths)

    print(np.median(widths))
    print(np.average(widths))

    start = lmr_low[0][1]
    end = lmr_low[-1][1]

    return start, end, median_width, lmr_low


def prepare_for_projection(image, angle):

    # Rotate the source image
    img = rotate(image, angle)

    # Threshold image - this is good for text no a white background.
    # may need tuning depending on image
    _, thresholded_image = cv2.threshold(img, 140, 255, cv2.THRESH_BINARY)

    return thresholded_image


def get_projection(image, vert=False):

    axis = 1
    if vert:
        axis = 0

    # Compute the sums of the rows - the projection
    # row_sums = sum_rows(image)
    row_sums = np.sum(image, axis=axis)

    # normalise to 0 to 255
    max_row = np.max(row_sums)
    row_sums = (row_sums / max_row) * 255
    return row_sums


def find_best_projection(img, start_angle, end_angle, vert, incr=0.5):

    min_score = sys.maxsize
    best_angle = -1
    best_projection = None

    angle = 0
    while angle <= end_angle:

        rotated_thresholded_img = prepare_for_projection(img, angle)

        # Compute the sums of the rows - the projection
        projection = get_projection(rotated_thresholded_img, vert)

        # because we are looking at text
        # rows between text (line breaks) should
        # have 0 value pixels if the skew is corrected
        # so we want the fewest rows that are > 0
        score = np.count_nonzero(projection)
        print(f"score: {score}  num rows: {len(projection)}")
        if score < min_score:
            min_score = score
            best_angle = angle
            best_projection = projection

        angle += incr

    return min_score, best_angle, best_projection


def rotate(img, angle):
    rows, cols = img.shape
    M = cv2.getRotationMatrix2D((cols / 2, rows / 2), angle, 1)
    dst = cv2.warpAffine(img, M, (cols, rows))
    return dst


def show_image(img, row_sums, line_breaks, vert=False):

    # draw the line breaks calculated from the
    # projection lows
    if not vert:
        for line_break_pos in line_breaks:
            img[line_break_pos, :] = 255
    else:
        for line_break_pos in line_breaks:
            img[:, line_break_pos] = 255

    img = 255 - img
    cv2.imshow('projection results', img)

    cv2.waitKey(0)


def load_image(file_path, squarify=False, invert=True):

    img = cv2.imread(file_path, 0)

    if invert:
        img = 255 - img

    if squarify:
        h, w = img.shape
        min_dim = min(h, w)
        img = img[0:min_dim, 0:min_dim]

    return img
