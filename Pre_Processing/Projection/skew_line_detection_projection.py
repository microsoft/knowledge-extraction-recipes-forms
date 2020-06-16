#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import projection as p


def main():

    image_file_path = './skewed_text.jpg'
    is_vert_projection = False

    image = p.load_image(image_file_path)

    # identify skew by rotating image and analysing the projection
    _, skew_angle, projection = p.find_best_projection(
        image,
        0,
        10,
        vert=is_vert_projection
    )

    # find the locations of text lines
    # lows are line breaks, highs are text
    lows, highs = p.find_runs(projection)

    # get the line break dimensions
    start, end, median_width, lmr_low = p.analyze_runs(lows)

    # take the mid point in the middle of a line break
    # where the width is greater than 3 (skips very narrow gaps)
    line_breaks = [int(lmr[1]) for lmr in lmr_low if lmr[3] > 3]

    # correct the skew of the original image
    image = p.rotate(image, skew_angle)

    # show the skew corrected image and the line breaks.
    p.show_image(
        image,
        projection,
        line_breaks,
        is_vert_projection)


if __name__ == "__main__":
    main()
