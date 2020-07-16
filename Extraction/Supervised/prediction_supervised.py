#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json
import os
import random
import shutil
import sys
import time
from datetime import datetime

import pandas as pd
from azure.storage.blob import (
    BlockBlobService
)
from dotenv import load_dotenv
from requests import get, post

load_dotenv()


def build_keys_json_object(keys, blob_name, anchor_key,
                           ground_truth_value, extracted_value, confidence, issuer_name,
                           actual_accuracy, extracted_page_number):
    """
    This function build the json object for the auto-labelling
    :param keys: The json object
    :param anchor_key: The field we are looking for
    :param blob_name: The name of the file we are processing
    :param ground_truth_value: The ground truth value for the field in questions
    :param confidence: The confidence score of the extracted value
    :param issuer_name: The unique identifier of the form
    :param actual_accuracy: The score we have inferred by comparing with the GT data
    :param extracted_value: The value extracted from the invoice
    :param extracted_page_number: The document page number the value was extracted from
    :return: The appended json dict and the found keys list
    """
    keys[issuer_name + ':' + blob_name].append({
        'key': anchor_key,
        'groundTruthValue': ground_truth_value,
        'extractedValue': extracted_value,
        'confidence': confidence,
        'actualAccuracy': actual_accuracy,
        'pageNumber': extracted_page_number
    })

    return keys


def extract_anchor_key_value(anchor_key, anchor_key_value):
    """

    :param anchor_key: The key field we are processing
    :param anchor_key_value: The value of the key
    :return: The value we have extracted
    """

    # TODO add custom logic and formatting to fields to be extracted
    if anchor_key == 'InvoiceNumber':
        # TODO basic formatting - add your own
        anchor_key_value = anchor_key_value.upper()
        anchor_key_value = anchor_key_value.strip("$")
        anchor_key_value = anchor_key_value.replace("-", "")
        anchor_key_value = anchor_key_value.replace(".", "")
        anchor_key_value = anchor_key_value.replace("'", "")

    # TODO Add any post-processing here
    anchor_key_value = str(anchor_key_value.replace(",", "")).lower().strip()
    anchor_key_value = anchor_key_value.replace(" ", "")
    anchor_key_value = anchor_key_value.replace("/", "")
    anchor_key_value = anchor_key_value.replace("-", "")

    return anchor_key_value


def gt_preprocessing(anchor_key, dfGTRow):
    """
    Simple formatting
    :param anchor_key: Key field we are extracting
    :param dfGTRow: The Ground Truth dataframe record for the file we are processing
    :return: The value extracted
    """
    # TODO add logic here for multi-page fields

    gt_key_value = str(dfGTRow.iloc[0][anchor_key]).lower().strip()

    return gt_key_value


def download_input_files_from_blob_storage(
        blob_service,
        container_name,
        input_folder_path,
        ext='pdf',
        num_sample=40):
    """

    :param blob_service: The blob service client
    :param container_name: The container we are working with
    :param input_folder_path: Folder path that contains the files for processing
    :param ext: Document extension - pdf
    :param num_sample: How many files we are sampling
    :return: list of files to process
    """

    blobs = blob_service.list_blobs(container_name)

    blob_names = []
    for blob in blobs:
        if not blob.name.endswith(ext):
            continue
        length = BlockBlobService.get_blob_properties(blob_service, container_name,
                                                      blob.name).properties.content_length
        # TODO at the time of writing this is the file size limit for a single form amend if needed
        if length >= 4000000:
            continue

        blob_names.append(blob.name)

        print(f"\t Blob name: {blob.name}")

    random.seed(16371580834230)

    sample_ok = False
    sample_decrement_counter = 0

    # Now we sample files for prediction
    while not sample_ok:
        try:
            little_blob_names = random.sample(blob_names, k=num_sample - sample_decrement_counter)
            sample_ok = True
        except Exception as not_enough_samples:
            print(f"{not_enough_samples} Reducing samples by 1")
            sample_decrement_counter += 1

    for blob_name in little_blob_names:
        print(f'Sampling file {blob_name}')
        blob_service.get_blob_to_path(container_name, blob_name, file_path=input_folder_path + '/' + blob_name)

    input_doc_files = [f for f in os.listdir(input_folder_path) if f.endswith(ext)]

    return input_doc_files


def process_folder_and_predict(
        keys,
        input_folder_path,
        ground_truth_df,
        model_id,
        issuer_name,
        input_doc_files,
        key_field_names,
        region,
        subscription_key,
):
    """
    Iterate through our storage accounts, download, correlate with Ground Truth and invoke downstream
    functions

    :param keys: Our data structure to store the results of every file prediction
    :param input_folder_path: The folder we are processing
    :param ground_truth_df: The dataframe with our ground truth
    :param model_id: The model associated with the files we are predicting
    :param issuer_name: The unique identifier of the form being processed
    :param input_doc_files: List of files to predict
    :param key_field_names: The fields we want to extract
    :param region: The region where Form Recognizer is deployed
    :param subscription_key: The Form Recognizer key
    :return:
    """

    # Let's get the fields we want to extract into a list
    anchor_keys = [f for f in key_field_names.split(',')]

    for input_file_name in input_doc_files:
        fieldcount = 0
        field_match_count = 0

        keys[issuer_name + ':' + input_file_name] = []

        try:

            before_call_time = datetime.now().strftime("%H:%M:%S")

            # Call to the Form Recognizer service
            resp = form_recognizerv2_analyse(region,
                                             subscription_key,
                                             model_id, input_file_name, input_folder_path)

            after_call_time = datetime.now().strftime("%H:%M:%S")

            short_file_name = str(input_file_name[:len(input_file_name) - 4])
            print(f'Searching for GT record {short_file_name}')

            # TODO add your file name identifier here from your Ground Truth
            df_gt_row = ground_truth_df[ground_truth_df['FILENAME'] == short_file_name]

            # loop through anchor keys and identify what was extracted by Form Recognizer
            for anchor_key in anchor_keys:
                anchor_key = anchor_key.strip()
                fields = resp['analyzeResult']['documentResults'][0]['fields']

                if anchor_key in fields:
                    fieldcount += 1

                    anchor_key_value = str(fields[anchor_key]['text'])
                    anchor_key_page_num = str(fields[anchor_key]['page'])
                    confidence = fields[anchor_key]['confidence']

                    if anchor_key == 'TOTAL':
                        # TODO add custom total formatting here
                        anchor_key_value = anchor_key_value.replace(",", "")

                    #  TODO add your custom formatting here if required
                    """
                    anchor_key_value = extract_anchor_key_value(
                        anchor_key,
                        anchor_key_value)
                    """
                    # TODO add your custom formatting/normalisation of your Ground Truth here
                    gt_original_value = str(df_gt_row.iloc[0][anchor_key])
                    gt_key_value = gt_preprocessing(anchor_key, df_gt_row)

                    # Does the post processed predicted field match the preprocessed ground truth
                    if anchor_key_value.lower().strip() == gt_key_value:
                        field_match_count += 1

                    print(f'{input_file_name} {anchor_key} Ground Truth: {gt_key_value.upper()} Extracted:'
                          f' {anchor_key_value.upper()}')

                    actual_accuracy = field_match_count / fieldcount

                    # Add key extraction to the output json
                    keys = build_keys_json_object(keys, input_file_name,
                                                  anchor_key, gt_original_value.strip(),
                                                  anchor_key_value.strip(),
                                                  confidence,
                                                  issuer_name,
                                                  actual_accuracy,
                                                  anchor_key_page_num)

            after_processing_time = datetime.now().strftime("%H:%M:%S")

            print(f"start call: {before_call_time} "
                  f"end_call_time: {after_call_time} "
                  f"end processing: {after_processing_time}")

        except Exception as e:
            exc_type, _, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f'Predict Error {e} {exc_type} {fname} {exc_tb.tb_lineno}')

    return keys


def get_prediction(region, subscription_key, blob_sas_url, model_id, predict_type):
    """Gets a prediction for a document with the Form Recognizer supervised model"""

    print(f"MODEL ID : {model_id}")
    headers = {
        "Content-Type": "application/pdf",
        "Ocp-Apim-Subscription-Key": subscription_key,
    }
    url = f"https://{region}.api.cognitive.microsoft.com/formrecognizer/v2.0/custom/models/{model_id}/analyze?includeTextDetails=True"
    result = None
    try:
        f = get(blob_sas_url)
        resp = post(url=url, data=f.content, headers=headers)

        if resp.status_code == 202:
            status_url = resp.headers['Operation-Location']
            print(f"Invoice analyze submitted. Operation Location: {status_url}")
            headers = {"Ocp-Apim-Subscription-Key": subscription_key}
            resp = get(url=status_url, headers=headers)
            print(resp.json())
            count = 0
            max_retry = 100
            while (count < max_retry and (resp.status_code == 200 or resp.status_code == 429) and (
                    resp.json()['status'] == 'running' or resp.json()['status'] == 'notStarted')):
                resp = get(url=status_url, headers=headers)
                time.sleep(1)
                count += 1
            print(resp.json()['status'])
            # print(resp.json())
            result = resp.json()['analyzeResult']
        else:
            print(f"Error during analysis: {str(resp.text)}")
    except Exception as e:
        print(f"Error analyzing invoice : {e}")

    prediction = {}
    if result != None:

        try:
            prediction['readResults'] = result['readResults']

            if predict_type == 'supervised':
                prediction['fields'] = []
                for key in result['documentResults'][0]['fields'].keys():
                    f = result['documentResults'][0]['fields'][key]
                    if f != None:
                        field = {}
                        field['label'] = key
                        field['text'] = f['text']
                        field['confidence'] = f['confidence']
                        field['boundingBox'] = f['boundingBox']
                        prediction['fields'].append(field)
            else:
                prediction['keyValuePairs'] = result['pageResults'][0]['keyValuePairs']

        except Exception as e:
            print(f"Prediction is invalid: {e}")

    return prediction


def form_recognizerv2_analyse(region, subscription_key, model_id, file_name, file_name_path):
    """
    Analyses a document with the Form Recognizer supervised model
    :param base_url: Prefix url for service
    :param subscription_key: CogSvc key
    :param model_id: Model associated with the document to predict
    :param file_name: File name we a predicting
    :param file_name_path: Path for file we are predicting
    :return: Prediction json response object
    """

    headers = {
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Content-Type": "application/pdf"
    }
    print(f'Evaluating against model_id {model_id}')

    url = f"https://{region}.api.cognitive.microsoft.com/formrecognizer/v2.0/custom/models/{model_id}/analyze?includeTextDetails=True"

    print(f'Predict {file_name} {file_name_path}')
    try:
        files = {'file': (file_name, open(file_name_path + '/' + file_name, 'rb'),
                          'application/pdf', {'Expires': '0'})}

        resp = post(url=url, files=files, headers=headers)
        if resp.status_code == 202:

            status_url = resp.headers['Operation-Location']
            headers = {"Ocp-Apim-Subscription-Key": subscription_key}
            resp = get(url=status_url, headers=headers)

            while not resp.json()['status'] == 'succeeded':
                resp = get(url=status_url, headers=headers)

            return resp.json()
        else:
            print(f"Error predicting {resp.text}")

    except Exception as e:
        exc_type, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(f'Predict error {e} {exc_type} {fname} {exc_tb.tb_lineno}')


def get_ground_truth():
    """
    TODO Add code to retrieve the ground truth from your datastore

    :return: Data frame with the Ground Truth
    """

    df = None
    models_df = None

    try:

        # TODO load your Ground Truth file
        df = pd.read_pickle(Config.GROUND_TRUTH_PATH, compression=None)
        # TODO load your model/issuer lookup
        models_df = pd.read_csv(Config.MODEL_LOOKUP, delimiter=',', compression=None)

    except Exception as e:
        exc_type, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(f'Error loading files {e} {exc_type} {fname} {exc_tb.tb_lineno}')

    return df, models_df


class Config:
    """
    Read from .env
    """
    TRAINING_END_POINT = os.environ.get("TRAINING_END_POINT")  # FR Training endpoint
    ANALYZE_END_POINT = os.environ.get("ANALYZE_END_POINT")  # OCR endpoint
    SUBSCRIPTION_KEY = os.environ.get("SUBSCRIPTION_KEY")  # CogSvc key
    STORAGE_ACCOUNT_NAME = os.environ.get("STORAGE_ACCOUNT_NAME")  # Account name for storage
    STORAGE_KEY = os.environ.get("STORAGE_KEY")  # The key for the storage account
    KEY_FIELD_NAMES = os.environ.get("KEY_FIELD_NAMES")  # The fields to be extracted e.g. invoicenumber,date,total
    SAS_PREFIX = os.environ.get("SAS_PREFIX")  # First part of storage account
    SAS = os.environ.get("SAS")  # SAS for storage train
    SAS_TEST = os.environ.get("SAS")  # SAS for storage test
    RUN_FOR_SINGLE_ISSUER = os.environ.get("RUN_FOR_SINGLE_ISSUER")  # If true process only this issuer
    DOC_EXT = os.environ.get("DOC_EXT")
    LANGUAGE_CODE = os.environ.get("LANGUAGE_CODE")  # The language we invoke Read OCR in only en supported now
    GROUND_TRUTH_PATH = os.environ.get("GROUND_TRUTH_PATH")  # This is the path to our Ground Truth
    LOCAL_WORKING_DIR = os.environ.get(
        "LOCAL_WORKING_DIR")  # The local temporary directory to which we write and remove
    CONTAINER_SUFFIX = os.environ.get(
        "CONTAINER_SUFFIX")  # The suffix name of the containers that store the training datasets
    LIMIT_TRAINING_SET = os.environ.get("LIMIT_TRAINING_SET")  # For testing models by file qty trained on
    COUNTRY_CODE = os.environ.get("COUNTRY_CODE")  # Our country code if needed
    MODEL_ID = os.environ.get("MODEL_ID")  # Run for a single model
    MODEL_LOOKUP = os.environ.get("MODEL_LOOKUP")  # The issuer to modelId lookup
    TRAIN_TEST = os.environ.get("TRAIN_TEST")  # Suffixes train or test to container name
    SAMPLE_NUMBER = os.environ.get("SAMPLE_NUMBER")  # Sample number of files for prediction
    KEY_FIELD_NAMES = os.environ.get("KEY_FIELD_NAMES")  # The fields we want to extract
    REGION = os.environ.get("REGION")  # The region Form Recognizer and OCR are deployed


def main():
    """
    :param argv: See input args below
    :return: Generates cluster file
    """

    rf = Config.LOCAL_WORKING_DIR
    # get the ground truth file for the key value extraction
    ground_truth_df, models_df = get_ground_truth()

    print(f'Downloaded GT and models {models_df}')

    block_blob_service = BlockBlobService(
        account_name=Config.STORAGE_ACCOUNT_NAME, account_key=Config.STORAGE_KEY)

    issuer_name = ''
    containers = block_blob_service.list_containers()
    for container in containers:
        keys = {}

        if len(Config.RUN_FOR_SINGLE_ISSUER) > 0:
            # This is where you control what it predicts
            temp_container_name = Config.RUN_FOR_SINGLE_ISSUER + Config.CONTAINER_SUFFIX + Config.TRAIN_TEST

            if temp_container_name not in container.name:
                continue

        if Config.CONTAINER_SUFFIX + Config.TRAIN_TEST \
                not in container.name or container.name[:1] != Config.COUNTRY_VENDOR_PREFIX:
            continue

        issuer_name = container.name[:9]
        print(f'Searching model file for issuer {issuer_name.strip()}')
        # TODO add your unique identifier key here
        model_df = models_df[models_df['Your unique key'] == int(issuer_name.strip())]

        if len(Config.MODEL_ID) > 0:
            model_id = Config.MODEL_ID
        else:
            print(f'Searching for {issuer_name} {len(model_df)}')
            model_id = model_df['modelId'].iloc[0]

        print(f'Model for vendor {issuer_name} is {model_id}')

        vendor_folder_path = f"{rf}/{container.name}"
        if not os.path.exists(vendor_folder_path):
            os.mkdir(vendor_folder_path)

        # Download the files to predict locally
        input_doc_files = download_input_files_from_blob_storage(
            block_blob_service, container.name, vendor_folder_path, Config.DOC_EXT,
            int(Config.SAMPLE_NUMBER))

        keys = process_folder_and_predict(
            keys,
            vendor_folder_path,
            ground_truth_df,
            model_id,
            issuer_name,
            input_doc_files,
            Config.KEY_FIELD_NAMES,
            Config.REGION
        )

        # Let's clean up to save space
        shutil.rmtree(vendor_folder_path)
        print(f'Predict finished')

        # Let's write our prediction file here
        # TODO add versioning here
        with open(Config.LOCAL_WORKING_DIR + '/supervised_predict_' + str(issuer_name) +
                  '_.json', 'w') as json_file:
            json.dump(keys, json_file)
            print('Wrote lookup file', str(issuer_name))


if __name__ == "__main__":
    main()
