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
    from shared_code import utils
except ModuleNotFoundError:
    from ..shared_code import utils


class TrainModel(BaseProcessor):
    def __init__(self):
        super(TrainModel, self).__init__()
    
    def files_processed(self, entities_status):
        return entities_status != None and entities_status.count('done') == len(entities_status)
    
    def get_training_data_path(self):
        return self.app_settings.storage_account_url + '/' + self.app_settings.container + self.app_settings.sas

    def train_and_save(self, doctype, training_data_path, use_label_file):

        if use_label_file == True:
            training_type = "supervised"
        else:
            training_type = "unsupervised"

        logging.info(f"{training_type} training started.")

        train_response = fr_helpers.train_model(self.app_settings.fr_region, self.app_settings.fr_key, training_data_path, doctype, use_label_file)

        if train_response != None:

            logging.info(f"{training_type} training done. Creating results file...")
            model_details = utils.get_model_details(train_response, training_type)

            if model_details != None:
                autolabel_results, csv_output = utils.create_results_files(model_details, doctype)
                autolabel_results_path = doctype + f'/autolabel_results_{training_type}.txt'
                storage_helpers.upload_blob(self.container_client, autolabel_results_path, autolabel_results)
                csv_output_path = doctype + f'/autolabel_{training_type}.csv'
                storage_helpers.upload_blob(self.container_client, csv_output_path, csv_output)
                logging.info("Done.")
                logging.info("Saving model details in models table...")
                entity = {
                        "PartitionKey": self.app_settings.environment + '_' + training_type, 
                        "RowKey": doctype, 
                        "modelId": model_details['model_id'],
                        "status": model_details['status'],
                        "avgAccuracy": model_details['accuracy'],
                        "date": model_details['date'],
                        "fieldsAccuracy": str(model_details['fields_accuracy'])
                        }
                storage_helpers.insert_or_replace_entity(self.table_service, self.app_settings.models_table, entity)
                return model_details

        return None
      
    def run(self, doctype, train_supervised, train_unsupervised):

        logging.info(f"Training will start. Training supervised: {train_supervised}, Training unsupervised:  {train_unsupervised}")

        training_data_path = self.get_training_data_path()
        result_supervised = None
        result_unsupervised = None

        if train_unsupervised == 'True':
            # Training unsupervised
            result_unsupervised = self.train_and_save(doctype, training_data_path, False)

        entities_status = storage_helpers.query_entities(self.table_service, self.app_settings.status_table, doctype)

        # If all files are processed, we can train the model
        if self.files_processed(entities_status):
            logging.info(f"All files processed for doc type {doctype}, supervised training will start...")

            
            if train_supervised == 'True':
                # Training supervised
                result_supervised = self.train_and_save(doctype, training_data_path, True)
           
            if result_supervised != None and result_unsupervised != None:

                return True, {
                    "text": "Training finished.",
                    "modelId_supervised": result_supervised['model_id'],
                    "status_supervised": result_supervised['status'],
                    "avgAccuracy": result_supervised['accuracy'],
                    "fieldsAccuracy": result_supervised['fields_accuracy'],
                    "modelId_unsupervised": result_unsupervised['model_id'],
                    "status_unsupervised": result_unsupervised['status']
                    }

            elif result_supervised != None and result_unsupervised == None:

                return True, {
                    "text": "Training supervised finished, training unsupervised failed.",
                    "modelId_supervised": result_supervised['model_id'],
                    "status": result_supervised['status'],
                    "avgAccuracy": result_supervised['accuracy'],
                    "fieldsAccuracy": result_supervised['fields_accuracy']
                    }

            elif result_supervised == None and result_unsupervised != None:

                return True, {
                    "text": "Training unsupervised finished, training supervised failed.",
                    "modelId_unsupervised": result_unsupervised['model_id'],
                    "status_unsupervised": result_unsupervised['status']
                    }            

            else:
                raise EnvironmentError("Error during training.")

        else:
          logging.info(f"Not all files are done processing for doc type {doctype}.")
          raise Warning( f"Processing not finished ({str(entities_status.count('done'))}/{str(len(entities_status))} files processed). \n Please retry later.",)

       
  