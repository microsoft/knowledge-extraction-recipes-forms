from PIL import Image
from PIL.PngImagePlugin import PngImageFile
from PIL.PpmImagePlugin import PpmImageFile


def get_image(image, clr_mode='L'):
    """Wrapper to retrieve and convert (color mode) PIL.Image object.

    Args:
        image (str or PIL.Image):
            Expects PIL.Image object or string path to image file
        clr_mode (str, optional):
            Color mode: 'RGB' or 'L' for grayscale. Defaults to 'L'.

    Returns:
        PIL.Image:
            Image object
    """
    assert(clr_mode in ['L', 'RGB'])
    image_type = type(image)
    pil_im = None

    if image_type is str:
        pil_im = Image.open(image).convert(clr_mode)
    elif image_type in [PngImageFile, Image.Image, Image, PpmImageFile]:
        pil_im = image.convert(clr_mode)
    else:
        raise ValueError("Unsupported type of input image argument")

    return pil_im


def resize_with_aspect_ratio(img, max_size=2800):
    """Helper function to resize image against the longer edge

    Args:
        img (PIL.Image):
            Image object to be resized
        max_size (int, optional):
            Max size of the longer edge in pixels.
            Defaults to 2800.

    Returns:
        PIL.Image:
            Resized image object
    """
    w, h = img.size
    aspect_ratio = min(max_size/w, max_size/h)
    resized_img = img.resize(
        (int(w * aspect_ratio), int(h * aspect_ratio))
    )
    return resized_img
