#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging

from azure.storage.blob import BlockBlobService, PublicAccess, ContainerPermissions, BlobPermissions, ContentSettings 

# Creates an Azure Blob Storage service


def create_blob_service(account_name, account_key):
    block_blob_service = None
    try:
        block_blob_service = BlockBlobService(account_name=account_name, account_key=account_key)
        logging.info("Blob service initialized successfully.")
    except Exception as e:
        logging.error("Could not instantiate blob service: %s"%e)
    return block_blob_service

# Lists all the blobs in a container


def list_blobs(blob_service, container_name):
    generator = None
    try:
        generator = blob_service.list_blobs(container_name)
        for blob in generator:
            print(blob.name)
    except Exception as e:
        logging.error("Could not list blobs in container %s: %s"%(container_name,e))
    return generator

# Retrieves file from blob storage


def get_blob(blob_service, container_name, blob_name):
    logging.info("Using blob service for account %s"%blob_service.account_name)
    try:
        blob = blob_service.get_blob_to_bytes(container_name, blob_name)
        logging.info("File %s successfully retrieved from blob storage."%blob_name)
        return blob
    except Exception as e:
        logging.error("Error retrieving file %s from blob storage: %s"%(blob_name,e))
        return None

# Uploads file to blob storage


def upload_blob(blob, blob_service, blob_name, container_name):
    try:
        settings = ContentSettings("image/jpeg")
        logging.info(f"Blob stream: {blob}")
        blob_service.create_blob_from_bytes(container_name=container_name, blob_name=blob_name, blob=blob.getvalue(), content_settings=settings)
        logging.info("File %s successfully uploaded to blob storage."%blob_name)
    except Exception as e:
        logging.error("Error uploading file %s to blob storage: %s"%(blob_name,e))
