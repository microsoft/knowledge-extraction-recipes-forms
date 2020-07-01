# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

# This function is not intended to be invoked directly. Instead it will be
# triggered by an orchestrator function.

import logging
import os

import filetype
import numpy as np
import cv2

from azure.storage.blob.aio import BlobServiceClient

from azure.storage.blob import ContentSettings


from . import clean_image


async def main(path: str):

    # Get blob name and container from path
    container = path.split("/")[0]
    blob = "/".join(path.split("/")[1:])

    logging.info(f"Orchestrator handled \n" f"Blob: {blob}\n" f"Container: {container}")

    # Download blob from blob storage
    blob_service_client = BlobServiceClient.from_connection_string(
        os.environ["StorageAccount"]
    )

    async with blob_service_client:

        blob_container_client = blob_service_client.get_container_client(container)
        blob_client = blob_container_client.get_blob_client(blob)

        # TODO Use /tmp directory for bigger files, to save memory in Azure Function
        download_stream = await blob_client.download_blob()
        blob_file = await download_stream.readall()

        # Detect filetype, to understand if conversion is required
        # Could be retrieved from blob metadata, but is not always accurate
        file_type = filetype.guess(blob_file)

        supported = ["image/jpeg", "image/bmp", "image/png", "image/tiff"]
        supported_after_conversion = ["application/pdf"]

        if (
            file_type.mime not in supported
            and file_type.mime not in supported_after_conversion
        ):
            logging.warning(
                "File with unsupported MIME type: %s %s", path, file_type.mime
            )
            return

        if file_type.mime in supported_after_conversion:
            # TODO Implement PDF to TIFF conversion
            logging.warning(
                "File with unsupported MIME type: %s %s", path, file_type.mime
            )
            return

        # Encode and decode buffer to OpenCV filetype
        try:
            form = np.fromstring(blob_file, np.uint8)
            image = cv2.imdecode(form, 1)

            normalized = clean_image.clean(image)

            finalBlob = cv2.imencode(f"blob.{file_type.extension}", normalized)[
                1
            ].tostring()

        except Exception:
            logging.error("OpenCV operation failed for: %s %s", path, file_type.mime)
            return

        # Write processed file to blob storage
        output_container = "input-cleaned"

        blob_container_client = blob_service_client.get_container_client(
            output_container
        )
        await blob_container_client.upload_blob(
            blob,
            finalBlob,
            content_settings=ContentSettings(content_type=file_type.mime),
        )

        newBlobPath = output_container + "/" + blob

        # Uncomment the following line if you want to have the origal blob removed after processing
        # blob_container_client.delete_blob(blob)

        return newBlobPath

