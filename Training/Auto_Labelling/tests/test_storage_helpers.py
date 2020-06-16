#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
import unittest
import os
import json
from mock import MagicMock, patch, mock_open

from shared_code import storage_helpers

from dotenv import load_dotenv
load_dotenv()

@pytest.mark.storagehelpers
class CreateTest(unittest.TestCase):

    sas = os.getenv('SAS_TOKEN')
    storage_account = os.getenv('STORAGE_ACCOUNT_NAME')
    storage_key = os.getenv('STORAGE_KEY')
    container = "tests"
    queue = "processing"
    table = "status"
    storage_url = f"https://{storage_account}.blob.core.windows.net"
    folder = "<ENTER FOLDER NAME>"
    label = "<ENTER LABEL>"

    def test_create_container_client_when_valid(self):
    
        # Expecting success when all parameters are valid
        container_client = storage_helpers.create_container_client(
                self.storage_url,
                self.container,
                self.sas)

        result = storage_helpers.list_blobs(container_client, self.folder)

        assert len(result) > 0

    def test_create_container_client_when_url_invalid(self):
    
        # Expecting failure when url is invalid
        container_client = storage_helpers.create_container_client(
                "https://urlinvalid.net",
                self.container,
                self.sas)

        result = storage_helpers.list_blobs(container_client, self.folder)

        assert len(result) == 0

    def test_create_container_client_when_container_invalid(self):
    
        # Expecting failure when container doesn't exist
        container_client = storage_helpers.create_container_client(
                self.storage_url,
                "abcd",
                self.sas)

        result = storage_helpers.list_blobs(container_client, self.folder)

        assert len(result) == 0

    def test_create_container_client_when_sas_invalid(self):
    
        # Expecting failure when sas token is invalid
        container_client = storage_helpers.create_container_client(
                self.storage_url,
                self.container,
                "abcd")

        result = storage_helpers.list_blobs(container_client, self.folder)

        assert len(result) == 0

    def test_create_table_service_when_valid(self):
    
        # Expecting success when all parameters are valid
        table_service = storage_helpers.create_table_service(
                self.storage_account,
                self.storage_key)

        result = storage_helpers.query_entities(table_service, self.table, self.label)

        assert result != None

    def test_create_table_service_when_account_invalid(self):
    
        # Expecting failure when storage account name is invalid
        table_service = storage_helpers.create_table_service(
                "aezaehzajebvheahez",
                self.storage_key)

        result = storage_helpers.query_entities(table_service, self.table, self.label)

        assert result == None

    def test_create_table_service_when_key_invalid(self):
    
        # Expecting failure when storage account key is invalid
        table_service = storage_helpers.create_table_service(
                self.storage_account,
                "abcd")

        result = storage_helpers.query_entities(table_service, self.table, self.label)

        assert result == None

    def test_create_queue_client_when_valid(self):
    
        # Expecting success when all parameters are valid
        result = storage_helpers.create_queue_client(
                self.storage_account,
                self.storage_key,
                self.queue)

        assert result != None


@pytest.mark.storagehelpers
class BlobStorageTest(unittest.TestCase):

    sas = os.getenv('SAS_TOKEN')
    storage_account = os.getenv('STORAGE_ACCOUNT_NAME')
    container = "tests"
    storage_url = f"https://{storage_account}.blob.core.windows.net"
    folder = "<ENTER FOLDER NAME>"
    container_client = storage_helpers.create_container_client(storage_url, container, sas)

    blob_name_folder = "<ENTER BLOB PATH WITH FOLDER>"
    blob_name_no_folder = "<ENTER BLOB PATH WITHOUT FOLDER>"
    root_folder = "<ENTER FOLDER NAME>"

    blob_name_upload = "test_upload.txt"
    blob_name_download = "test.txt"
    blob_data = "Hello"

    def test_list_blobs_when_valid(self):
    
        # Expecting success when all parameters are valid
        result = storage_helpers.list_blobs(
                self.container_client, 
                self.folder)

        assert len(result) > 0

    def test_list_blobs_when_folder_invalid(self):
    
        # Expecting failure when folder doesn't exist
        result = storage_helpers.list_blobs(
                self.container_client, 
                "abcd")

        assert len(result) == 0
    
    def test_blob_name_contains_folder_when_yes(self):
    
        # Expecting True when blob name contains a folder
        result = storage_helpers.blob_name_contains_folder(
                self.blob_name_folder)

        assert result == True    

    def test_blob_name_contains_folder_when_no(self):
    
        # Expecting False when blob name doesn't contain a folder
        result = storage_helpers.blob_name_contains_folder(
                self.blob_name_no_folder)

        assert result == False

    def test_get_blob_root_folder_when_folder_is_there(self):
    
        # Expecting root folder
        result = storage_helpers.get_blob_root_folder(
                self.blob_name_folder)

        assert result == self.root_folder
    
    def test_get_blob_root_folder_when_folder_is_not_there(self):
    
        # Expecting root folder
        result = storage_helpers.get_blob_root_folder(
                self.blob_name_no_folder)

        assert result == None

    def test_list_doctype_folders_when_valid(self):
    
        # Expecting folders back when container client is valid
        result = storage_helpers.list_doctype_folders(
                self.container_client)

        assert len(result) > 0

    def test_list_doctype_folders_when_invalid(self):
    
        # Expecting no folders back when container client is invalid
        result = storage_helpers.list_doctype_folders(
                None)

        assert len(result) == 0

    def test_list_folders_when_valid(self):
    
        # Expecting folders back when container client is valid
        result = storage_helpers.list_folders(
                self.container_client)

        assert len(result) > 0

    def test_list_folders_when_invalid(self):
    
        # Expecting no folders back when container client is invalid
        result = storage_helpers.list_folders(
                None)

        assert len(result) == 0

    def test_upload_blob_when_valid(self):
    
        # Expecting success when all parameters are valid
        result = storage_helpers.upload_blob(
                self.container_client,
                self.blob_name_upload,
                self.blob_data)

        assert result == True

    def test_upload_blob_when_container_client_invalid(self):
    
        # Expecting failure when container client is invalid
        result = storage_helpers.upload_blob(
                None,
                self.blob_name_upload,
                self.blob_data)

        assert result == False
    
    def test_download_text_blob_when_valid(self):
    
        # Expecting success when all parameters are valid and we are downloading text
        result = storage_helpers.download_blob(
                self.container_client,
                self.blob_name_download,
                "text")

        assert result != None

    def test_download_bytes_blob_when_valid(self):
    
        # Expecting success when all parameters are valid and we are downloading bytes
        result = storage_helpers.download_blob(
                self.container_client,
                self.blob_name_download)

        assert result != None

    def test_download_text_blob_when_container_client_invalid(self):
    
        # Expecting failure when container client is invalid and we are downloading text
        result = storage_helpers.download_blob(
                None,
                self.blob_name_download,
                "text")

        assert result == None

    def test_download_bytes_blob_when_container_client_invalid(self):
    
        # Expecting failure when container client is invalid and we are downloading bytes
        result = storage_helpers.download_blob(
                None,
                self.blob_name_download)

        assert result == None

    def test_download_text_blob_when_blob_name_invalid(self):
    
        # Expecting failure when blob name is invalid and we are downloading text
        result = storage_helpers.download_blob(
                self.container_client,
                "abcd",
                "text")

        assert result == None

    def test_download_bytes_blob_when_blob_name_invalid(self):
    
        # Expecting failure when blob name is invalid and we are downloading bytes
        result = storage_helpers.download_blob(
                self.container_client,
                "abcd")

        assert result == None



@pytest.mark.storagehelpers
class TableStorageTest(unittest.TestCase):

    storage_account = os.getenv('STORAGE_ACCOUNT_NAME')
    storage_key = os.getenv('STORAGE_KEY')
    table_status = "status"
    table_model = "models"
    label = "test"
    blob_name = "test.pdf"
    model = "<ENTER MODEL NAME>"
    partition_key = "<ENTER PARTITION KEY>"
    table_service = storage_helpers.create_table_service(storage_account, storage_key)
    entity = {'PartitionKey': label, 'RowKey': blob_name, 'status': 'new'}


    def test_insert_or_replace_entity_when_valid(self):
        
        # Expecting success when all parameters are valid
        result = storage_helpers.insert_or_replace_entity(
                self.table_service, 
                self.table_status,
                self.entity)

        assert result == True

    def test_insert_or_replace_entity_when_entity_invalid(self):
        
        entity_invalid = {'Name': self.blob_name, 'status': 'new'}
        # Expecting failure when entity is invalid
        result = storage_helpers.insert_or_replace_entity(
                self.table_service, 
                self.table_status,
                entity_invalid)

        assert result == False

    def test_insert_or_replace_entity_when_table_service_invalid(self):
        
        # Expecting failure when table service is invalid
        result = storage_helpers.insert_or_replace_entity(
                None, 
                self.table_status,
                self.entity)

        assert result == False

    def test_insert_or_replace_entity_when_table_invalid(self):
        
        # Expecting failure when table is invalid
        result = storage_helpers.insert_or_replace_entity(
                self.table_service, 
                "abcd",
                self.entity)

        assert result == False

    def test_query_entity_status_when_valid(self):
        
        # Expecting success when all parameters are valid
        result = storage_helpers.query_entity_status(
                self.table_service, 
                self.table_status,
                self.label,
                self.blob_name)

        assert result != None

    def test_query_entity_status_when_table_service_invalid(self):
        
        # Expecting failure when table service is invalid
        result = storage_helpers.query_entity_status(
                None, 
                self.table_status,
                self.label,
                self.blob_name)

        assert result == None

    def test_query_entity_status_when_table_invalid(self):
        
        # Expecting failure when table is invalid
        result = storage_helpers.query_entity_status(
                self.table_service, 
                "abcd",
                self.label,
                self.blob_name)

        assert result == None

    def test_query_entity_status_when_partition_key_invalid(self):
        
        # Expecting failure when partition key is invalid
        result = storage_helpers.query_entity_status(
                self.table_service, 
                self.table_status,
                "abcd",
                self.blob_name)

        assert result == None

    def test_query_entity_status_when_row_key_invalid(self):
        
        # Expecting failure when row key is invalid
        result = storage_helpers.query_entity_status(
                self.table_service, 
                self.table_status,
                self.label,
                "abcd")

        assert result == None

    def test_query_entity_model_when_valid(self):
        
        # Expecting success when all parameters are valid
        result = storage_helpers.query_entity_model(
                self.table_service, 
                self.table_model,
                self.partition_key,
                self.model)

        assert result != None

    def test_query_entity_model_when_table_service_invalid(self):
        
        # Expecting failure when table service is invalid
        result = storage_helpers.query_entity_model(
                None, 
                self.table_model,
                self.partition_key,
                self.model)

        assert result == None

    def test_query_entity_model_when_table_invalid(self):
        
        # Expecting failure when table is invalid
        result = storage_helpers.query_entity_model(
                self.table_service, 
                "abcd",
                self.partition_key,
                self.model)

        assert result == None

    def test_query_entity_model_when_partition_key_invalid(self):
        
        # Expecting failure when partition key is invalid
        result = storage_helpers.query_entity_model(
                self.table_service, 
                self.table_model,
                "abcd",
                self.model)

        assert result == None

    def test_query_entity_model_when_row_key_invalid(self):
        
        # Expecting failure when row key is invalid
        result = storage_helpers.query_entity_model(
                self.table_service, 
                self.table_model,
                self.partition_key,
                "abcd")

        assert result == None

    def test_query_entities_when_valid(self):
        
        # Expecting success when all parameters are valid
        result = storage_helpers.query_entities(
                self.table_service, 
                self.table_status,
                self.label)

        assert result != None

    def test_query_entities_when_table_service_invalid(self):
        
        # Expecting failure when table service is invalid
        result = storage_helpers.query_entities(
                None, 
                self.table_status,
                self.label)

        assert result == None

    def test_query_entities_when_table_invalid(self):
        
        # Expecting failure when table is invalid
        result = storage_helpers.query_entities(
                self.table_service, 
                "abcd",
                self.label)

        assert result == None

    def test_query_entities_when_partition_key_invalid(self):
        
        # Expecting result to be empty when partition key is invalid
        result = storage_helpers.query_entities(
                self.table_service, 
                self.table_status,
                "abcd")

        assert len(result) == 0


@pytest.mark.storagehelpers
class QueueStorageTest(unittest.TestCase):

    storage_account = os.getenv('STORAGE_ACCOUNT_NAME')
    storage_key = os.getenv('STORAGE_KEY')
    queue = "test"
    queue_client = storage_helpers.create_queue_client(storage_account, storage_key, queue)
    message = "Hello"

    def test_add_queue_message_when_valid(self):
    
        # Expecting success when all parameters are valid
        result = storage_helpers.add_queue_message(
                self.queue_client,
                self.message)

        assert result != None

    def test_add_queue_message_when_queue_client_invalid(self):
    
        # Expecting failure when queue client is invalid
        result = storage_helpers.add_queue_message(
                None,
                self.message)

        assert result == None

    def test_get_queue_message_when_valid(self):

        storage_helpers.add_queue_message(
                self.queue_client,
                self.message)
                
        # Expecting success when queue client is valid
        result = storage_helpers.get_queue_message(
                self.queue_client)

        assert result != None

    def test_get_queue_message_when_queue_client_invalid(self):

        # Expecting failure when queue client is invalid
        result = storage_helpers.get_queue_message(
                None)

        assert result == None

    def test_get_queue_message_str_when_valid(self):

        storage_helpers.add_queue_message(
                self.queue_client,
                self.message)
                
        # Expecting success when queue client is valid
        result = storage_helpers.get_queue_message_str(
                self.queue_client)

        assert result != None

    def test_get_queue_message_str_when_queue_client_invalid(self):

        # Expecting failure when queue client is invalid
        result = storage_helpers.get_queue_message_str(
                None)

        assert result == None


    def test_delete_queue_message_when_valid(self):

        msg = storage_helpers.add_queue_message(
                self.queue_client,
                self.message)
                
        # Expecting success when queue client is valid
        result = storage_helpers.delete_queue_message(
                self.queue_client,
                msg)

        assert result == True

    def test_delete_queue_message_when_queue_client_invalid(self):

        msg = storage_helpers.add_queue_message(
                self.queue_client,
                self.message)
                
        # Expecting failure when queue client is invalid
        result = storage_helpers.delete_queue_message(
                None,
                msg)

        assert result == False

    def test_delete_queue_message_when_msg_invalid(self):

        # Expecting failure when queue client is invalid
        result = storage_helpers.delete_queue_message(
                self.queue_client,
                None)

        assert result == False


    
