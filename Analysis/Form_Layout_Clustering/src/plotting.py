import numpy as np
from matplotlib import patches as patches
from matplotlib import pyplot as plt
from PIL import Image
from sklearn.manifold import TSNE

from common import get_image, resize_with_aspect_ratio


def visualize_features(X, Y, use_tsne=True):
    """
    Visualize feature vectors

    Args:
        X (array):
            Features array of shape (n_samples, n_features)
        Y (array):
            Labels array of shape (n_samples,)

        use_tsne (bool, optional):
            Use TSNE or not.
            Defaults to True.
    """
    labels = np.unique(Y)
    markers = ['o', 'x', '+', 'v', '^']
    colors = [
        'red', 'blue', 'cyan',
        'green', 'yellow'
    ]

    if use_tsne:
        X = TSNE(random_state=1).fit_transform(X)

    plt.figure(figsize=(10, 10))
    for label, color, marker in zip(labels, colors, markers):
        class_mask = Y == label
        plt.scatter(
            X[class_mask][:, 0],
            X[class_mask][:, 1],
            c=color, marker=marker
        ) 

    plt.legend(labels, fontsize=20)
    plt.show()


def plot_img_ocr_bb(
        img, ocr_data,
        resize_max_size=2800,
        apply_ocr_orientation=False):
    """
    Displays document image with OCR text overlayed on top

    Args:
        img (str or PIL.Image):
            Image to use
        ocr_data (dict):
            OCR data in dictionary format
        resize_max_size (int, optional):
            Max size of the longer edge.
            Defaults to 2800.
        apply_ocr_orientation (bool, optional):
            Use OCR orientation data to align image.
            Defaults to False.
    """

    d = ocr_data
    pil_im = get_image(img)

    if apply_ocr_orientation:
        pil_im = pil_im.rotate(d['osd']['orientation'], expand=True)

    pil_im = resize_with_aspect_ratio(pil_im, resize_max_size)

    plt.figure(figsize=(15, 15))
    # Display the image
    plt.imshow(pil_im, cmap='gray')

    n_boxes = len(d['level'])
    par_num = -1
    line_num = -1
    linestyle = '-'
    for i in range(n_boxes):
        (x, y, w, h) = (d['left'][i], d['top'][i],
                        d['width'][i], d['height'][i])

        if par_num != d['par_num'][i]:
            rect_color = 'g'
            line_width = 3
            linestyle = '--'
# {'-', '--', '-.', ':', '', (offset, on-off-seq), ...}
        elif line_num != d['line_num'][i]:
            rect_color = 'b'
            line_width = 2
            linestyle = '-.'
        else:
            rect_color = 'r'
            line_width = 1
            linestyle = '-'
        par_num = d['par_num'][i]
        line_num = d['line_num'][i]

        # Create a Rectangle patch
        rect = patches.Rectangle(
            (x, y), w, h,
            linewidth=line_width,
            edgecolor=rect_color,
            linestyle=linestyle,
            facecolor='none')

        # Add the patch to the Axes
        plt.gca().add_patch(rect)

        plt.text(
            x, y,
            d['text'][i].replace('$', '\$'),
            color='r', fontsize=9)

    plt.show()
