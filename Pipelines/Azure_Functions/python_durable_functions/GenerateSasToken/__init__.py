# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

# This function is not intended to be invoked directly. Instead it will be
# triggered by an orchestrator function.

import logging
import os
from datetime import datetime, timedelta

from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, ResourceTypes, AccountSasPermissions

def main(path: str) -> str:
    # Get blob name and container from path
    container = path.split('/')[0]
    blob = "/".join(path.split('/')[1:])

    blob_service_client = BlobServiceClient.from_connection_string(os.environ["StorageAccount"])
    blob_container_client = blob_service_client.get_container_client(container)
    blob_client = blob_container_client.get_blob_client(blob)

    # Generate a token valid for 15 minutes
    sas_token = generate_blob_sas(
        account_name=blob_container_client.account_name,
        account_key=blob_container_client.credential.account_key,
        container_name=blob_container_client.container_name,
        blob_name=blob,
        permission=AccountSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(minutes=15),
    )
    sas_url = f"{blob_client.url}?{sas_token}"

    return sas_url
