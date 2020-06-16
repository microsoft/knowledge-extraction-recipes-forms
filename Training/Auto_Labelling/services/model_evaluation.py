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
    from shared_code import model_evaluation
except ModuleNotFoundError:
    from ..shared_code import model_evaluation


class ModelEvaluation(BaseProcessor):
    def __init__(self):
        super(ModelEvaluation, self).__init__()
    
    def run(self, doctype, reuse = False):
        folders = storage_helpers.list_doctype_folders(self.container_client)
        
        if(doctype in folders):
            logging.info(f"Found {doctype} folder in storage.")
            testing_path = doctype + '/test'
            blobs = storage_helpers.list_blobs(self.container_client, testing_path)
            if(len(blobs) > 0):
               
                # Getting model ID from doctype name
                partition_key = self.app_settings.environment + '_supervised'
                
                model_id = storage_helpers.query_entity_model(self.table_service, self.app_settings.models_table, partition_key, doctype)

                if model_id != None:
                    logging.info(f"Found model id {model_id} for doc type {doctype}")

                    evaluation_output_path = doctype + '/evaluation_file.json'

                    if (reuse == 'False'):
                        logging.warning("REUSE FALSE")
                        # Batch predictions on all test blobs
                        logging.info(f"Predicting for test set...")

                        predictions, count_analyzed, count_total = fr_helpers.batch_predictions(blobs, model_id, self.app_settings.storage_account_url, self.app_settings.container, self.app_settings.sas, self.app_settings.fr_region, self.app_settings.fr_key)
                        evaluation = model_evaluation.evaluate(predictions,  self.app_settings.gt_path,  self.app_settings.lookup_path, count_analyzed, count_total)
                        evaluation_file = json.dumps(evaluation)
                        storage_helpers.upload_blob(self.container_client, evaluation_output_path, evaluation_file)

                    else:
                        logging.info(f"Evaluation file for doc type {doctype} already created, getting it from storage.")
                        evaluation_file = storage_helpers.download_blob(self.container_client, evaluation_output_path, 'text')
                        if(evaluation_file != None):
                            evaluation = json.loads(evaluation_file)

                    if(evaluation != None):

                        model_eval_json, mismatches = model_evaluation.create_eval_file(evaluation, model_id, self.app_settings.lookup_path)   
                        response = {}
                        response['text'] = f"Evaluation for doc type {doctype} done."
                        response['eval'] = model_eval_json.copy()
                        
                        model_eval_json['mismatches'] = mismatches
                        model_eval_file = json.dumps(model_eval_json)
                        model_eval_output_path = doctype + '/model_eval.json'
                        storage_helpers.upload_blob(self.container_client, model_eval_output_path, model_eval_file)

                        # Bell sound when the process finishes
                        print("\a")
    
                        return response
                    
                else:
                    logging.error(f"Could not continue as model id could not be retrieved.")
                    raise EnvironmentError(f"Could not retrieve model id.")
                
            else:
                logging.warning(f"Didn't find any testing files in storage for {doctype}")
                raise Warning(f"No test files.")

        else:
            logging.warning(f"Didn't find {doctype} folder in storage.")
            raise Warning(f"{doctype} not in storage.")




