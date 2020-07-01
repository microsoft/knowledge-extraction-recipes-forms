# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

# This function is not intended to be invoked directly. Instead it will be
# triggered by an orchestrator function.

import os
import logging
import json

from azure.storage.blob.aio import BlobServiceClient
from azure.storage.blob import ContentSettings


async def main(forminfo) -> str:

    result = forminfo.get("result")
    path = forminfo.get("path")

    # Get blob name and container from path
    container = path.split("/")[0]
    blob = "/".join(path.split("/")[1:])

    # Download blob from blob storage
    blob_service_client = BlobServiceClient.from_connection_string(
        os.environ["StorageAccount"]
    )

    async with blob_service_client:
        filename = blob + ".json"
        blob_container_client = blob_service_client.get_container_client("output")

        await blob_container_client.upload_blob(
            filename,
            json.dumps(result),
            content_settings=ContentSettings(content_type="application/json"),
        )

    return f"output/{blob}!"
