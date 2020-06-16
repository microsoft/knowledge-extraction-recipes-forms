#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging
import os
import json
from .base_processor import BaseProcessor
try:
    from shared_code import storage_helpers
except ModuleNotFoundError:
    from ..shared_code import storage_helpers
try:
    from shared_code import fr_helpers
except ModuleNotFoundError:
    from ..shared_code import fr_helpers
try:
    from shared_code import autolabeling
except ModuleNotFoundError:
    from ..shared_code import autolabeling

class ProcessDoc(BaseProcessor):
    def __init__(self):
        super(ProcessDoc, self).__init__()
    
    def run(self, blob_name, skip_status_table = False, gt_df = None):
        if self.container_client != None and self.table_service != None:
            file_content = storage_helpers.download_blob(self.container_client, blob_name)

            # Check document status to see if it was already processed
            doctype = blob_name.split('/')[0]
            file_name = blob_name.split('/')[-1]
            status = "new"

            if(skip_status_table == False):
                status = storage_helpers.query_entity_status(self.table_service, self.app_settings.status_table, doctype, file_name)
            # If status = "done", we do nothing, if status = "ocr_done", we only find labels
            if status != 'done':

                ocr_output_path = blob_name + '.ocr.json'
                if status != 'ocr-done':
                    # Creating OCR file for document
                    logging.info(f"Creating OCR file for document {blob_name}...")
                    analyze_result = fr_helpers.analyze_layout(self.app_settings.fr_region, self.app_settings.fr_key, file_content, blob_name)
                    analyze_result_string = json.dumps(analyze_result)
                    storage_helpers.upload_blob(self.container_client, ocr_output_path, analyze_result_string)
                    # Updating status
                    if(skip_status_table == False):
                        entity = {'PartitionKey': doctype, 'RowKey': file_name, 'status': 'ocr-done'}
                        if storage_helpers.insert_or_replace_entity(self.table_service, self.app_settings.status_table, entity):
                            logging.info(f"Updated {blob_name} status in status table.")
                        else:
                            logging.error(f"Could not update {blob_name} status in status table.")
                else:
                    logging.info(f"OCR file for document {blob_name} already created, getting it from storage.")
                    ocr_file = storage_helpers.download_blob(self.container_client, ocr_output_path, 'text')
                    if(ocr_file != None):
                        analyze_result = json.loads(ocr_file)
                
                # Creating labels file for document
                if analyze_result != None:
                    key_field_names = self.fields
                    labels_result, keys = autolabeling.analyze_labels(gt_df if gt_df is not None else self.app_settings.gt_path, blob_name, analyze_result, key_field_names, self.app_settings.lookup_path)
                    logging.info(keys)
                    if  labels_result != None and len(keys) > 1:
                        labels_output_path = blob_name + '.labels.json'
                        labels_result_string = json.dumps(labels_result)
                        storage_helpers.upload_blob(self.container_client, labels_output_path, labels_result_string)
                        # Updating status
                        if(skip_status_table == False):
                            entity = {'PartitionKey': doctype, 'RowKey': file_name, 'status': 'done'}
                            if storage_helpers.insert_or_replace_entity(self.table_service, self.app_settings.status_table, entity):
                                logging.info(f"Updated {blob_name} status in status table.")
                            else:
                                logging.error(f"Could not update {blob_name} status in status table.")

                else:
                    logging.error(f"Could not continue processing for blob {blob_name} as analyze result is missing.")

     
  