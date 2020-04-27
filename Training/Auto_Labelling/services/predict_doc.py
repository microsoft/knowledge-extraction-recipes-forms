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

class PredictDoc(BaseProcessor):
    def __init__(self):
        super(PredictDoc, self).__init__()

    def get_predict(self, doctype, sas_url, predict_type):

        # Getting model ID from doc type
        partition_key = self.app_settings.environment + '_' + predict_type
        model_id = storage_helpers.query_entity_model(self.table_service, self.app_settings.models_table, partition_key, doctype)

        # Getting prediction result
        prediction = fr_helpers.get_prediction(self.app_settings.fr_region, self.app_settings.fr_key, sas_url, model_id, predict_type)

        return prediction

    
    def run(self, doctype, sas_url):

        prediction_supervised = self.get_predict(doctype, sas_url, "supervised")
        prediction_unsupervised = self.get_predict(doctype, sas_url, "unsupervised")
       
        response = {}
        if len(prediction_supervised) > 0 and len(prediction_unsupervised) > 0:
            response['text'] = "Successfully retrieved prediction (supervised and unsupervised)."
            response['fields'] = prediction_supervised['fields']
            response['keyValuePairs'] = prediction_unsupervised['keyValuePairs']
            response['readResults'] = prediction_supervised['readResults']
        elif len(prediction_supervised) > 0 and len(prediction_unsupervised) == 0:
            response['text'] = "Successfully retrieved prediction (supervised only)."
            response['fields'] = prediction_supervised['fields']
            response['readResults'] = prediction_supervised['readResults']
        elif len(prediction_supervised) == 0 and len(prediction_unsupervised) > 0:
            response['text'] = "Successfully retrieved prediction (unsupervised only)."
            response['keyValuePairs'] = prediction_unsupervised['keyValuePairs']
            response['readResults'] = prediction_unsupervised['readResults']
        else:
            response['text'] = "Could not retrieve prediction"

        if prediction_supervised != None:
            return response
        else:
            raise EnvironmentError("Error during prediction.")




