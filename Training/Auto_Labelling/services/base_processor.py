#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import collections
from abc import ABCMeta, abstractmethod

try:
    from shared_code import storage_helpers
except ModuleNotFoundError:
    from ..shared_code import storage_helpers

AppSettings = collections.namedtuple('AppSettings', 'container storage_account_name storage_account_url storage_key sas status_table models_table fr_region fr_key gt_path lookup_path environment')

class BaseProcessor(object, metaclass=ABCMeta):

    @abstractmethod
    def __init__(self):
        self.get_app_settings()
        self.get_storage_clients()
        ####################################
        # TODO: CHANGE KEYS TO LOOK FOR HERE 
        ####################################
        self.fields = ["Total amount", "Delivery amount", "Date", "Name", "Address line 1", "Address line 2", "Address country", "Item name", "Item price"]

    def get_app_settings(self):
        container = os.getenv('DATA_CONTAINER')
        storage_account_name = os.getenv('STORAGE_ACCOUNT_NAME')
        storage_account_url = f"https://{storage_account_name}.blob.core.windows.net"
        storage_key = os.getenv('STORAGE_KEY')
        sas = os.getenv('SAS_TOKEN')
        status_table = os.getenv('STATUS_TABLE')
        models_table = os.getenv('MODELS_TABLE')
        fr_region = os.getenv('FR_REGION')
        fr_key = os.getenv('FR_KEY')
        gt_path = os.getenv('GT_PATH')
        lookup_path = os.getenv('LOOKUP_FILE')
        environment = os.getenv('ENVIRONMENT')
        self.app_settings = AppSettings(container=container, storage_account_name=storage_account_name, storage_account_url=storage_account_url, storage_key=storage_key, sas=sas, status_table=status_table, models_table=models_table, fr_region=fr_region, fr_key=fr_key , gt_path=gt_path, lookup_path=lookup_path, environment=environment)

    def get_storage_clients(self):
        self.container_client = storage_helpers.create_container_client(self.app_settings.storage_account_url, self.app_settings.container, self.app_settings.sas)
        self.table_service = storage_helpers.create_table_service(self.app_settings.storage_account_name, self.app_settings.storage_key)
        self.queue_client = storage_helpers.create_queue_client(self.app_settings.storage_account_name, self.app_settings.storage_key, "processing")
