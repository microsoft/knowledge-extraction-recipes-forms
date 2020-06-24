# This function is not intended to be invoked directly. Instead it will be
# triggered by an orchestrator function.

import logging

import os
import io

import azure.functions as func

import filetype
import numpy as np
import cv2

# pylint: disable=unsubscriptable-object
def main(path: str, inputBlob: func.InputStream, outputBlob: func.Out[func.InputStream]) -> str:

    logging.warning(
        f"Orchestrator handled \n"
        f"Name: {inputBlob.name}\n"
        f"Blob Size: {inputBlob.length} bytes"
    )

    outputBlob.set(inputBlob)
    form = inputBlob.read()

    # # Check filetype of blob, should be validated in an earlier step normally
    file_type = filetype.guess(form)

    # # Clean image using OpenCV
    try:
        form = np.fromstring(form, np.uint8)
        # image = cv2.imdecode(form, 1)
        # normalized = clean_form.clean(image)
    except IOError:
        return

    # # Write to preprocessing/out
    # finalBlob = cv2.imencode(inputBlob.name, normalized)[1].tostring()


    return f"Specified path is {path}!"