#!/usr/bin/env python
# coding: utf-8

# # The AutoLablleing Process Demo

# This document describes how to implement the autolabelling process for the Supervised version of Forms Recognizer. By using an autolabelling approach we are able to reduce but not remove the need for a human-in-the-loop. It is strongly recommended that manual labelling still takes place for poorly performing models, but the need for manual labelling should be significantly reduced.
# 
# We will be referencing code from here https://github.com/microsoft/knowledge-extraction-recipes-forms/tree/master/Training/Auto_Labelling/basic_implementation

# # In summary, the autolabelling process will implement the following steps:
# 
# 1. Prepare the files by converting them from TIF --> JPG --> PDF if required
# 2. Create Storage Containers with a specific naming convention and uploaded the converted files - do this for train and test datasets
# 3. Iterate through every container
# 4. Load the corresponding ground truth record (GT) for an invoice
# 5. Retrieve the values from the GT for the keys we want to extract/tag/label
# 6. Call Read Layout (OCR) for the invoice if no OCR file exists for the invoice
# 7. Search through both the line and word level of the OCR file with formatting to find the ground truth values for the keys to be extracted.
# 8. If a value is found, get the corresponding page, height, width and bounding box attributes for the original unformatted OCR value
# 9. Generate the corresponding ocr.labels.json for the invoice
# 10. Upload the label and json files to the Storage Container and train the Supervised version of Forms Recognizer.

# In[1]:


import sys, os
from os import path
__prep_file__ = 'autolabel_prepare_file.py'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__prep_file__), '..')))

__common_file__ = 'autolabel_common.py'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__common_file__), '..')))

__train_file__ = 'autolabel_training.py'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__train_file__), '..')))

__root_common__ = 'common.py'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__root_common__), '..')))

__predict_supervised__ = 'Supervised/prediction_supervised.py'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__predict_supervised__), '..')))

__scoring_supervised__ = 'Scoring/evaluation_gt.py'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__scoring_supervised__), '..')))

from azure.storage.blob import (
    BlockBlobService,
    ContainerPermissions
)

from Training.Auto_Labelling.basic_implementation.autolabel_common import find_anchor_keys_in_form
from Training.Auto_Labelling.basic_implementation.autolabel_prepare_files import create_container, upload_blobs_to_container
from Training.Auto_Labelling.basic_implementation.autolabel_training import process_folder, select_best_training_set, \
    form_recognizerv2_train
from Extraction.Supervised.prediction_supervised import download_input_files_from_blob_storage, process_folder_and_predict
from Evaluation.Scoring.evaluation_gt import print_results, load_json

from common.common import is_phrase_in
import pandas as pd
import json

# ## Set up our environment variables

# In[2]:


class Config:
    """
    Read from .env file
    """
    FORMS_PATH = '../Data/Invoices/Train' #  The directory where our files to process are
    DOC_EXT = '.pdf'
    STORAGE_ACCOUNT_NAME = 'spformsrecognizer'  # Account name for storage
    STORAGE_KEY = 'zK7GXLZc5buXNX8ps2hb4LDTqOGRhUxx2s0PCROzHUQHS3BcceSocZwitQlkaHdNL7NjXl73n06Hszgl8yIp5Q=='  # The key for the storage account
    LOCAL_WORKING_DIR =  '../Data/Invoices/temp' # The local temporary directory to which we write and remove
    TRAIN_TEST = 'train'  # Suffixes train or test to container name
    CONTAINER_SUFFIX = 'autolabelv1'  # The suffix name of the containers that store the training datasets
    KEY_FIELD_NAMES = os.environ.get("KEY_FIELD_NAMES")  # The fields to be extracted e.g. invoicenumber,date,total
    GROUND_TRUTH_PATH = os.environ.get("GROUND_TRUTH_PATH")  # This is the path to our Ground Truth
    LANGUAGE_CODE = 'en'
    REGION = 'eastus'  # The region Form Recognizer and OCR are deployed
    SUBSCRIPTION_KEY = '05e053d185984175931176e7b88fb536'  # CogSvc key
    MULTI_PAGE_FIELDS = os.environ.get("MULTI_PAGE_FIELDS")  # These fields appear over multiple pages
    MINIMUM_LABELLED_DATA = os.environ.get("MINIMUM_LABELLED_DATA")  # The minimum number of well labelled samples to
    #  train on
    SAS_TEST = os.environ.get("SAS")  # SAS for storage test


# ## Step 1: Convert files

# ### We do not need to convert the files as they are already in pdf format

# ## Step 2: Create Storage Containers with a specific naming convention and uploaded the converted files - Train dataset

# In[3]:

def main():

    # Get a list on the files to process
    files = [f for f in os.listdir(Config.FORMS_PATH) if f.endswith(Config.DOC_EXT)]

    # Create the BlockBlockService that the system uses to call the Blob service for the storage account.
    block_blob_service = BlockBlobService(
        account_name=Config.STORAGE_ACCOUNT_NAME, account_key=Config.STORAGE_KEY)

    for file_name in files:

        container_name = Config.CONTAINER_SUFFIX + Config.TRAIN_TEST
        print(f"Uploading to blob {container_name}")

        # Create container if it doesn't exist and get container sas url
        _, _ = create_container(block_blob_service, Config.STORAGE_ACCOUNT_NAME, container_name)

        # Upload to container
        upload_blobs_to_container(block_blob_service, Config.FORMS_PATH, container_name, Config.DOC_EXT)


    # ## Step 2: Create Storage Containers with a specific naming convention and uploaded the converted files - Test dataset

    # In[4]:


    Config.FORMS_PATH = '../Data/Invoices/Test' #  The directory where our files to process are
    Config.TRAIN_TEST = 'test'  # Suffixes train or test to container name


    # Get a list on the files to process
    files = [f for f in os.listdir(Config.FORMS_PATH) if f.endswith(Config.DOC_EXT)]

    # Create the BlockBlockService that the system uses to call the Blob service for the storage account.
    block_blob_service = BlockBlobService(
        account_name=Config.STORAGE_ACCOUNT_NAME, account_key=Config.STORAGE_KEY)

    for file_name in files:

        container_name = Config.CONTAINER_SUFFIX + Config.TRAIN_TEST
        print(f"Uploading to blob {container_name}")

        # Create container if it doesn't exist and get container sas url
        _, _ = create_container(block_blob_service, Config.STORAGE_ACCOUNT_NAME, container_name)

        # Upload to container
        upload_blobs_to_container(block_blob_service, Config.FORMS_PATH, container_name, Config.DOC_EXT)


    # ## Step 3: Iterate through every container

    # ### We now want to get our training datasets, as we are only processing one vendor for this demo, we only want to process the training dataset for AutoLabelling

    # In[5]:


    # Revert back to Train dataset
    Config.TRAIN_TEST = 'train'  # Suffixes train or test to container name


    # In[6]:


    containers = block_blob_service.list_containers()
    for container in containers:
        if (Config.CONTAINER_SUFFIX + Config.TRAIN_TEST
                not in container.name):
            continue

        assert container.name == Config.CONTAINER_SUFFIX + Config.TRAIN_TEST
        print(container.name)


    # ### Now we are going to specific the fields we want to extract, these must match the values in your ground truth, so let's load our ground truth file to see what these are

    # ## Step 4: Load the corresponding ground truth record (GT) for an invoice

    # In[7]:


    Config.GROUND_TRUTH_PATH = '../Data/Invoices/Invoice_GT.csv'  # This is the path to our Ground Truth
    ground_truth_df = pd.read_csv(Config.GROUND_TRUTH_PATH, sep=",")
    ground_truth_df.head()


    # ### We can see our columns names above, these are keys we want to work with, so let's populate the environment variable KEY_FIELD_NAMES

    # In[8]:


    Config.KEY_FIELD_NAMES = 'INVOICE_NUM, INVOICE_DATE, VENDOR, BILL_TO, TOTAL, VAT_ID, VENDOR_ZIP, BILL_TO_ZIP'
    key_field_names = Config.KEY_FIELD_NAMES.split(',')


    # # Steps 5 - 9: AutoLabel and generate the OCR and labels files

    # In[9]:


    vendor_folder_path_pass1 = f"{Config.LOCAL_WORKING_DIR}/pass1"
    vendor_folder_path_pass2 = f"{Config.LOCAL_WORKING_DIR}/pass2"

    # create training files for all input files
    pass_level, num_files, num_ground_truth = process_folder(
        vendor_folder_path_pass1,
        vendor_folder_path_pass2,
        key_field_names,
        Config.DOC_EXT,
        Config.LANGUAGE_CODE,
        ground_truth_df,
        block_blob_service,
        Config.CONTAINER_SUFFIX + Config.TRAIN_TEST,
        Config.REGION,
        Config.SUBSCRIPTION_KEY)


    # ## Now we select the best training set from our two passes

    # Because we are AutoLabelling, we can afford to label more than the minimum 5 forms if we have the data. This can result in a model more robust

    # In[ ]:


    Config.MINIMUM_LABELLED_DATA = 5


    # In[ ]:


    selected_training_set = select_best_training_set(pass_level, vendor_folder_path_pass1, vendor_folder_path_pass2, Config.MINIMUM_LABELLED_DATA)

    # Upload the best training set to the container
    upload_blobs_to_container(block_blob_service, selected_training_set, Config.CONTAINER_SUFFIX + Config.TRAIN_TEST,
                              '.json')
    print(f"Uploaded files to blob {Config.CONTAINER_SUFFIX + Config.TRAIN_TEST} training set {selected_training_set}")

    # Train the model on the optimised dataset
    Config.SAS = """?sp=rl&st=2020-06-01T17:19:35Z&se=2021-01-07T17:19:00Z&sv=2019-10-10&sr=c&sig=zNncMSV0Vi7kcX0kWg4c3VsUHk6dMRAafWv5L7%2F4MW0%3D"""

    Config.SAS_PREFIX = 'https://spformsrecognizer.blob.core.windows.net/'

    sasurl = Config.SAS_PREFIX + Config.CONTAINER_SUFFIX + Config.TRAIN_TEST + Config.SAS
    train_response = form_recognizerv2_train(Config.REGION,
                                             Config.SUBSCRIPTION_KEY,
                                             sasurl)
    print(f"Trained {train_response}")
    modelId = train_response['modelInfo']['modelId']
    print(f"\nModelId is {modelId}")
    accuracy = train_response['trainResult']['averageModelAccuracy']
    print(f"Average Model Accuracy {accuracy}")

    for field in train_response['trainResult']['fields']:
        print(f"Field {field['fieldName']} accuracy {field['accuracy']}")

    # Sample number of files for prediction - used when you have many files to predict and want to sample
    Config.SAMPLE_NUMBER = 2

    # Revert back to test dataset
    Config.TRAIN_TEST = 'test'  # Suffixes train or test to container name

    Config.FORMS_PATH = '../Data/Invoices/Test'  # The directory where our files to process are

    # Download the files to predict locally
    input_doc_files = download_input_files_from_blob_storage(
        block_blob_service, Config.CONTAINER_SUFFIX + Config.TRAIN_TEST, Config.FORMS_PATH, Config.DOC_EXT,
        int(Config.SAMPLE_NUMBER))

    keys = {}

    Config.REGION = 'eastus'

    modelId = '0c9408db-7580-4a76-8130-87a979a82162'

    keys = process_folder_and_predict(
        keys,
        Config.FORMS_PATH,
        ground_truth_df,
        modelId,
        'autolabelv1',
        input_doc_files,
        Config.KEY_FIELD_NAMES,
        Config.REGION,
        Config.SUBSCRIPTION_KEY
    )

    result_file = Config.FORMS_PATH + '/supervised_predict_autolabelv1.json'

    # Let's save the result file
    with open(result_file, 'w') as json_file:
        json.dump(keys, json_file)

    issuer_results = load_json(result_file)

    Config.KEY_FIELD_NAMES = 'INVOICE_NUM, INVOICE_DATE, VENDOR, BILL_TO, TOTAL, VAT_ID, VENDOR_ZIP, BILL_TO_ZIP'
    key_field_names = Config.KEY_FIELD_NAMES.split(',')

    accuracy, FormNumberAccuracy = print_results('autolabelv1', key_field_names, issuer_results,
                                                 'autolabelv1.txt', ground_truth_df, Config.FORMS_PATH)

    with open(os.path.join('../Data/Invoices/', 'Testautolabelv1.txt'), 'w') as txt_results:
        res = txt_results.read()

    print(res)

if __name__ == "__main__":
    main()



