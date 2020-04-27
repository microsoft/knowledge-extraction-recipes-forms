import pytest
import unittest
import os
import json
from mock import MagicMock, patch, mock_open

from shared_code import fr_helpers
from shared_code import storage_helpers

from dotenv import load_dotenv
load_dotenv()

@pytest.mark.frhelpers
class TrainModelTest(unittest.TestCase):

    region = os.getenv('FR_REGION')
    key = os.getenv('FR_KEY')
    sas = os.getenv('SAS_TOKEN')
    storage_account = os.getenv('STORAGE_ACCOUNT_NAME')
    container_valid = "tests"
    container_invalid = "tests2"

    training_url_valid = f"https://{storage_account}.blob.core.windows.net" + '/' + container_valid + sas
    training_url_invalid = f"https://{storage_account}.blob.core.windows.net" + '/' + container_invalid + sas
    label = "<ENTER LABEL>"

    def test_train_model_supervised_when_valid(self):
    
        # Expecting success when all parameters are valid and we are training using the labels file
        result = fr_helpers.train_model(
                self.region,
                self.key,
                self.training_url_valid,
                self.label)

        assert result['modelInfo']['status'] == 'ready'  


    #### Not testing this if not necessary because it takes a while ####
    # def test_train_model_unsupervised_when_valid(self):
    
    #     # Expecting success when all parameters are valid and we are training in unsupervised mode (without the labels file)
    #     result = fr_helpers.train_model(
    #             self.region,
    #             self.key,
    #             self.training_url,
    #             self.label,
    #             False)

    #     assert result['modelInfo']['status'] == 'ready' 

    def test_train_model_supervised_when_training_url_invalid(self):
    
        # Expecting failure when the training container doesn't contain the right folders
        result = fr_helpers.train_model(
                self.region,
                self.key,
                self.training_url_invalid,
                self.label)

        assert result['modelInfo']['status'] == 'invalid'

    def test_train_model_supervised_when_region_invalid(self):
    
        # Expecting failure when region is invalid
        result = fr_helpers.train_model(
                "easteurope",
                self.key,
                self.training_url_valid,
                self.label)

        assert result == None

    def test_train_model_supervised_when_key_invalid(self):
    
        # Expecting failure when key is invalid
        result = fr_helpers.train_model(
                self.region,
                "abcd",
                self.training_url_valid,
                self.label)

        assert result == None

    def test_train_model_supervised_when_label_invalid(self):
    
        # Expecting failure when label name is invalid
        result = fr_helpers.train_model(
                self.region,
                self.key,
                self.training_url_valid,
                "abcd")

        assert result['modelInfo']['status'] == 'invalid'


@pytest.mark.frhelpers
class PredictionsTest(unittest.TestCase):

    region = os.getenv('FR_REGION')
    key = os.getenv('FR_KEY')
    sas = os.getenv('SAS_TOKEN')
    models_table = os.getenv('MODELS_TABLE')
    storage_account = os.getenv('STORAGE_ACCOUNT_NAME')
    storage_key = os.getenv('STORAGE_KEY')
    storage_url = f"https://{storage_account}.blob.core.windows.net"

    label = "<ENTER LABEL>"
    container = "tests"
    partition_key = label[0].upper()

    table_service = storage_helpers.create_table_service(storage_account, storage_key)
    container_client = storage_helpers.create_container_client(storage_url, container, sas)
    model_id = storage_helpers.query_entity_model(table_service, models_table, partition_key, label)

    filename = "<ENTER FILE NAME>"

    test_url_valid = f"https://{storage_account}.blob.core.windows.net/{container}/{label}/test/{filename}{sas}"
    test_url_invalid = f"https://{storage_account}.blob.core.windows.net/{container}/{label}/test/filename{sas}"

    testing_path = label + '/test'
    blobs = storage_helpers.list_blobs(container_client, testing_path)

    def test_predict_supervised_when_valid(self):
    
        # Expecting fields back when all parameters are valid
        result = fr_helpers.get_prediction(
                self.region,
                self.key,
                self.test_url_valid,
                self.model_id,
                "supervised")

        assert len(result) > 0  

    def test_predict_supervised_when_url_invalid(self):
    
        # Expecting empty result when url is invalid
        result = fr_helpers.get_prediction(
                self.region,
                self.key,
                self.test_url_invalid,
                self.model_id,
                "supervised")

        assert len(result) == 0  

    def test_predict_supervised_when_region_invalid(self):
    
        # Expecting empty result when region is invalid
        result = fr_helpers.get_prediction(
                "easteurope",
                self.key,
                self.test_url_valid,
                self.model_id,
                "supervised")

        assert len(result) == 0  

    def test_predict_supervised_when_key_invalid(self):
    
        # Expecting empty result when key is invalid
        result = fr_helpers.get_prediction(
                self.region,
                "abcd",
                self.test_url_valid,
                self.model_id,
                "supervised")

        assert len(result) == 0  

    def test_predict_supervised_when_model_id_invalid(self):
    
        # Expecting empty result when the model id is invalid
        result = fr_helpers.get_prediction(
                self.region,
                self.key,
                self.test_url_valid,
                "abcd",
                "supervised")

        assert len(result) == 0  

    def test_batch_predict_supervised_when_valid(self):
    
        # Expecting predictions back when all parameters are valid
        result,_,_ = fr_helpers.batch_predictions(
                self.blobs,
                self.model_id,
                self.storage_url,
                self.container,
                self.sas,
                self.region,
                self.key)

        assert len(result) > 0  

    def test_batch_predict_supervised_when_url_invalid(self):
    
        # Expecting no predictions back when storage url is invalid
        result,_,_ = fr_helpers.batch_predictions(
                self.blobs,
                self.model_id,
                "invalidurl.net",
                self.container,
                self.sas,
                self.region,
                self.key)

        assert len(result) == 0 
    
    def test_batch_predict_supervised_when_blobs_empty(self):
    
        # Expecting no predictions back when the list of blobs is empty
        result,_,_ = fr_helpers.batch_predictions(
                [],
                self.model_id,
                self.storage_url,
                self.container,
                self.sas,
                self.region,
                self.key)

        assert len(result) == 0 


@pytest.mark.frhelpers
class AnalyzeLayoutTest(unittest.TestCase):

    region = os.getenv('FR_REGION')
    key = os.getenv('FR_KEY')
    filepath = "./tests/test_data/sample_pdf.pdf"
    with open(filepath, 'rb') as f:
        file_content = f.read()

    filename = "Sample PDF"

    def test_analyze_layout_when_valid(self):
    
        # Expecting success when all parameters are valid
        result = fr_helpers.analyze_layout(
                self.region,
                self.key,
                self.file_content,
                self.filename)

        assert result != None  

    def test_analyze_layout_when_file_invalid(self):
    
        # Expecting failure when file content is invalid
        result = fr_helpers.analyze_layout(
                self.region,
                self.key,
                "file",
                self.filename)

        assert result == None 
    
    def test_analyze_layout_when_region_invalid(self):
    
        # Expecting failure when region is invalid
        result = fr_helpers.analyze_layout(
                "easteurope",
                self.key,
                self.file_content,
                self.filename)

        assert result == None 

    def test_analyze_layout_when_key_invalid(self):
    
        # Expecting failure when key is invalid
        result = fr_helpers.analyze_layout(
                self.region,
                "abcd",
                self.file_content,
                self.filename)

        assert result == None 