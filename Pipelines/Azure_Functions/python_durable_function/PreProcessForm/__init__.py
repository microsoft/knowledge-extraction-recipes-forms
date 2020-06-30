# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

# This function is not intended to be invoked directly. Instead it will be
# triggered by an orchestrator function.

import logging

import os
import io

import azure.functions as func

import filetype
import numpy as np
import cv2

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from . import clean_image


def main(path: str):

    # Get blob name and container from path
    container = path.split("/")[0]
    blob = "/".join(path.split("/")[1:])

    logging.warning(
        f"Orchestrator handled \n" f"Blob: {blob}\n" f"Container: {container}"
    )

    # Download blob from blob storage
    blob_service_client = BlobServiceClient.from_connection_string(
        os.environ["StorageAccount"]
    )
    blob_container_client = blob_service_client.get_container_client(container)
    blob_client = blob_container_client.get_blob_client(blob)

    # TODO Use /tmp directory for bigger files, to save memory
    download_stream = blob_client.download_blob()
    blob_file = download_stream.readall()

    # Detect filetype, see if conversion is required
    file_type = filetype.guess(blob_file)

    supported = ["image/jpeg", "image/bmp", "image/png", "image/tiff"]
    supported_after_conversion = ["application/pdf"]

    if file_type.mime in supported_after_conversion:
        logging.warning("Unsupported file detected: %s %s", path, file_type.mime)

    logging.warning("Supported file detected: %s %s", path, file_type.mime)

    # Clean image using OpenCV
    try:
        form = np.fromstring(blob_file, np.uint8)
        image = cv2.imdecode(form, 1)
        normalized = clean_image.clean(image)
        finalBlob = cv2.imencode(blob, normalized)[1].tostring()

    except IOError:
        logging.error("OpenCV operation failed for: %s", path)
        return

    blob_container_client = blob_service_client.get_container_client("input-cleaned")
    blob_container_client.upload_blob(blob, finalBlob)
    newBlobPath = "input-cleaned/" + blob

    # Uncomment the following line if you want to have the origal blob removed after processing
    # blob_container_client.delete_blob(blob)

    return path, newBlobPath

