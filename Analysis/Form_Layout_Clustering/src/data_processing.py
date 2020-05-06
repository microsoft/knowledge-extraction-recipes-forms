import json
import os
import tempfile
import traceback

import pdf2image
import pytesseract
from matplotlib import pyplot as plt
from PyPDF2 import PdfFileReader
from pytesseract import Output, TesseractError

from common import get_image, resize_with_aspect_ratio

# Use this
if os.name == 'nt':
    tesseract_path = 'C:/Program Files/Tesseract-OCR/tesseract.exe'
    print("Setting Tesseract path to: %s" % tesseract_path)
    print("WARNING: Please verify if this is a correct path for Tesseract")
    pytesseract.pytesseract.tesseract_cmd = tesseract_path


def pdf_to_images(
        pdf_path,
        save_images=False,
        overwrite=False,
        pages_to_process_limit=10,
        output_path=None):
    """Converts PDF files (based on a path provided) into PIL.Image objects

    Args:
        pdf_path (string):
            Path to the PDF file
        save_images (bool, optional):
            Save or don't save PIL.Image as PNG files locally.
            Output filepath follows below pattern:
            `<pdf_path>_N.png`
            - `pdf_path` is the path to original PDF file without .PDF ext
            - `N` is the number of the page in a document
            Defaults to False.
        overwrite (bool, optional): 
            Overwrite existing files when saving images.
            Defaults to False.
        pages_to_process_limit (int, optional):
            Some documents have hundreds of pages and in order to save
            some processing time you can set a threshold that ignores
            PDFS with more than N number of pages.
            Defaults to 10.
        output_path (str, optional):
            You can provide your own output path for images to be saved.
            Defaults to None.

    Returns:
        list<PIL.Image>:
            List of image objects representing each page of PDF file.
    """

    with open(pdf_path, 'rb') as f:
        pdffile = PdfFileReader(f)
        number_of_pages = pdffile.getNumPages()
    if number_of_pages <= pages_to_process_limit:
        images = pdf2image.convert_from_path(pdf_path)
        if save_images:
            if output_path is None:
                output_path = pdf_path
            for i in range(len(images)):
                save = True
                save_img_path = output_path.replace(".pdf", "_%s.png" % i)
                if os.path.exists(save_img_path):
                    save = overwrite

                if save:
                    images[i].save(save_img_path)
        return images
    else:
        raise Exception("Too many pages in document...")


def image_to_text(
        image,
        resize_max_size=2800,
        fix_orientation=True,
        return_image=False,
        hocr=False,
        save_output=False,
        output_file=None,
        continue_on_error=True,
        verbose=1):
    """Extracts text from an image using Tesseract OCR

    Args:
        image (str or PIL.Image):
            Input image to extract text from
        resize_max_size (int, optional):
            Max size for the longer edge of an image to resize to.
            Defaults to 2800.
        fix_orientation (bool, optional):
            Use Tesseract OSD info to fix image orientation.
            Defaults to True.
        return_image (bool, optional):
            Return PIL.Image after conversions and resizing
            Defaults to False.
        hocr (bool, optional):
            Use HOCR output format.
            Defaults to False.
        save_output (bool, optional):
            Save OCR output using JSON or HOCR formats.
            Defaults to False.
        output_file (str, optional):
            Specify the path for OCR output to be saved to.
            Defaults to None.
        continue_on_error (bool, optional):
            Especially for batch processing it makes sense to
            continue on error rather than breaking the process.
            Defaults to True.
        verbose (int, optional):
            Options:
            0 - no messages
            1 - only error msgs
            2 - everything.
            Defaults to 1.

    Returns:
        OCR output (dict/json or XML/HOCR format) and PIL.Image after transformations if `return_image==True`  # NOQA E501
        
    """
    if verbose == 2:
        print("===============")
        print("Processing image: ", image)

    try:
        pil_im = get_image(image)

        if resize_max_size is not None:
            pil_im = resize_with_aspect_ratio(pil_im, resize_max_size)
            if verbose == 2:
                print("Resized image to max size: ", resize_max_size)
                print("Output size: ", pil_im.size)

        if fix_orientation:
            osd = pytesseract.image_to_osd(pil_im, output_type=Output.DICT)
            rotation = osd['orientation']
            if rotation > 0:
                pil_im = pil_im.rotate(rotation, expand=True)
            if verbose == 2:
                print("Rotated image by: ", rotation)

        data = None
        output_ext = ".json"
        if hocr:
            data = pytesseract.image_to_pdf_or_hocr(
                pil_im, lang='eng', extension='hocr')
            output_ext = ".xml"
        else:
            data = pytesseract.image_to_data(
                pil_im, lang='eng',
                output_type=Output.DICT)
            if fix_orientation:
                data['osd'] = osd
            output_ext = ".json"

        if (output_file is not None or (type(image) is str)) and save_output:
            output_file = output_file if output_file is not None else image
            # ensure propper extension
            output_file = os.path.splitext(output_file)[0] + output_ext
            # I was getting weird error and replacing slashes helped so:
            output_file = output_file.replace(
                "\\", "/").replace("\\", "/")
            with open(output_file, 'wb') as file_object:
                if hocr:
                    file_object.write(data)
                else:
                    # Save dict data into the JSON file.
                    json.dump(data, file_object)
                if verbose == 2:
                    print("Saved OCR to output file:", output_file)
        elif save_output:
            if verbose == 2:
                print(("Saving output was requested but output file path was not provided.\n"  # NOQA E501
                        "Please provide correct path as `output_file` param."))

        if return_image:
            if verbose == 2:
                print("Returning complete OCR data + processed PIL Image..")
            return data, pil_im
        else:
            if verbose == 2:
                print("Returning complete OCR data..")
            return data

    except Exception as e:
        if not continue_on_error:
            raise e
        if verbose > 0:
            print('--------------------------------------')
            print('Error caught while processing: ', image)
            print('Returning empty string!')
            print('+++')
            print('Error msg:', e)
            print('Error traceback: \n\n', traceback.format_exc())
            print('--------------------------------------')

        if return_image:
            return "", None
        else:
            return ""
