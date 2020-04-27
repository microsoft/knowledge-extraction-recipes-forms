import json
import os
import random
import shutil
import sys

import pandas as pd
from azure.storage.blob import (
    BlockBlobService
)
from dotenv import load_dotenv
from requests import get, post

from .common import compute_partial_ratio, compute_ratio

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


def form_recognizerv1_score(base_url, subscription_key, model_id,
                            file_name, file_name_path, keys=""):
    """
    Analyzes the input file based on the trained model from Form Recognizer.
    :param base_url: Url prefix for service
    :param subscription_key: CogSvc key
    :param model_id: Model associated with doc to score
    :param file_name: Name of file we are scoring
    :param file_name_path: Path to file we are scoring
    :param keys: The filter keys
    :return: Response object
    """

    print(f'Filtering on keys {keys}')
    headers = {
        "Ocp-Apim-Subscription-Key": subscription_key,
    }

    file = file_name_path + '/' + file_name
    print(f'Predicting unsupervised {file}')

    with open(file, 'rb') as data_bytes:

        try:
            # Here we filter on keys if required
            if len(keys) > 0:
                # TODO change this baseurl when the service is out of preview
                url = base_url + "/formrecognizer/v1.0-preview/custom/models/" + model_id + "/analyze?keys=" + keys
            else:
                url = base_url + "/formrecognizer/v1.0-preview/custom/models/" + model_id + "/analyze"
            resp = post(url=url, data=data_bytes, headers=headers)
            print(f"Response status code: {resp.status_code}")

            return resp.status_code, resp.json()

        except Exception as e:
            exc_type, _, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f'Predict error {e} {exc_type} {fname} {exc_tb.tb_lineno}')


def build_unsupervised_filter_keys(synonyms, np_filter_keys, filter_keys):
    """
    Here are building the filter keys to ensure we retrieve only the key value
    pairs we are interested in extracting
    :param synonyms: The taxonomy file we have loaded
    :param np_filter_keys: No punctuation in keys
    :param filter_keys: Punctuation in keys
    :return: A string of filter keys to be used a query param in the request
    """
    keys = []
    keys_string = ''
    # Let's get the fields we want to extract into a list
    anchor_keys = Config.ANCHOR_KEYS.split()

    for anchor in anchor_keys:
        # TODO add any keys here to help resolve the correct taxonomy value
        for synonym in synonyms['Your synonym file']:
            if synonym[0].lower() in np_filter_keys:
                idx = np_filter_keys.index(synonym[0].lower())

                # We are going to build a querystring to pass our keys
                keys.append(filter_keys[idx])
            else:
                for filter_key in np_filter_keys:
                    score = compute_ratio(anchor, filter_key.lower())
                    pscore = compute_partial_ratio(anchor, filter_key.lower())
                    total = score + pscore / 2

                    # TODO set a threshold here that makes sense for your data
                    if total > 120:
                        idx = np_filter_keys.index(filter_key)
                        keys.append(filter_keys[idx])

    keys = list(set(keys))

    # This is our querystring of unique taxonomy key values
    for i, key in enumerate(keys):
        if i == 0:
            keys_string += 'keys=' + key
        else:
            keys_string += '&keys=' + key

    return keys_string


def form_recognizer_get_keys(base_url, subscription_key, model_id):
    """
    Gets a list of keys for a model from Form Recognizer API.
    :param base_url: The prefix to the FR service
    :param subscription_key: CogSvc key
    :param model_id: The model associated with the prediction
    :return: json object with FR keys for the model
    """

    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    # TODO change this baseurl when the service is out of preview
    url = base_url + "/formrecognizer/v1.0-preview/custom/models/" + model_id + "/keys"
    print('Unsupervised get keys', url)
    try:
        resp = get(url=url, headers=headers)
        print("Response status code: %d" % resp.status_code)
        if resp.status_code == 200:
            return resp.status_code, resp.json()
    except Exception as e:
        print(str(e))


def get_synonym_key_from_value(synonyms, value):
    """

    :param synonyms: The synonym or taxonomy file
    :param value: The value we have retrieved
    :return: The key to the value
    """
    key = None
    # Let's get the fields we want to extract into a list
    anchor_keys = Config.ANCHOR_KEYS.split()

    for anchor_key in anchor_keys:
        # TODO add your synomyn lookup keys here
        for _, key_item in enumerate(synonyms['Your Taxonomy key values']):
            if key_item[0].lower() == value.lower():
                key = anchor_key
                break

    return key


def process_folder_and_predict_unsupervised(
        keys,
        input_folder_path,
        ext,
        language_code,
        ground_truth_df,
        blob_service,
        container_name,
        model_id,
        issuer_name,
        synonyms):
    """
    Iterate through our storage accounts, download, correlate with Ground Truth and invoke downstream
    functions

    :param keys: Our data structure to store the results of every file prediction
    :param input_folder_path: The folder we are processing
    :param ext: File extension to process - pdf
    :param language_code: Currently only en
    :param ground_truth_df: The dataframe with our ground truth
    :param blob_service: The blob service client
    :param container_name: Name of the container we are processing
    :param model_id: The model associated with the files we are predicting
    :param issuer_name: The unique identifier of the form
    :param synonyms: The taxonomy object
    :return:
    """

    # Let's get the fields we want to extract into a list
    anchor_keys = Config.ANCHOR_KEYS.split()

    blobs = blob_service.list_blobs(container_name)
    blob_names = [blob.name for blob in blobs if blob.name.endswith('pdf')]

    # We randomly sample from the set of files for prediction
    random.seed(16371580834230)

    little_blob_names = random.choices(blob_names, k=Config.SAMPLE_NUMBER)
    for blob_name in little_blob_names:
        print(f'Sampling file {blob_name}')
        blob_service.get_blob_to_path(container_name, blob_name, file_path=input_folder_path + '/' + blob_name)

    input_doc_files = [f for f in os.listdir(input_folder_path) if f.endswith(ext)]

    # TODO add any additional mapping here to help resolve the outputs of Form Recognizer
    key_map = {'Invoice Number': 'InvoiceNumber', 'Invoice Date': 'InvoiceDate', 'Currency': 'Currency'}
    # TODO ...

    for input_file_name in input_doc_files:
        fieldcount = 0
        field_match_count = 0

        keys[issuer_name + ':' + input_file_name] = []

        filter_keys = form_recognizer_get_keys(Config.UNSUPERVISED_ANALYZE_END_POINT,
                                               Config.SUBSCRIPTION_KEY,
                                               model_id)

        filter_keys = filter_keys[1]['clusters']['0']
        np_filter_keys = [x.lower() for x in filter_keys]

        keys_string = build_unsupervised_filter_keys(anchor_keys, synonyms, np_filter_keys,
                                                     filter_keys)

        resp = form_recognizerv1_score(Config.UNSUPERVISED_ANALYZE_END_POINT,
                                       Config.SUBSCRIPTION_KEY,
                                       model_id, input_file_name, input_folder_path,
                                       keys=keys_string)

        try:
            print(f'Searching for GT record {str(input_file_name[:len(input_file_name) - 4])}')

            # TODO add your unique filename identifier here
            dfGTRow = ground_truth_df[ground_truth_df['Your Filename identifier'] ==
                                      str(input_file_name[:len(input_file_name) - 4])]

            # TODO note the response format it may change beyond preview
            for key in resp[1]['pages'][0]['keyValuePairs']:
                for text in key['key']:
                    if len(key['value']) > 0:
                        print(f"Getting synonym key {key['key'][0]['text'].lower().replace(':', '')}")
                        original_key = get_synonym_key_from_value(synonyms, key['key'][0]['text']
                                                                  .lower().replace(":", ""))

                        try:
                            anchor_key = key_map[original_key]
                            print(key['key'][0]['text'], '-->', key['value'][0]['text'],
                                  anchor_key, text)
                            anchor_key_value = key['value'][0]['text']
                        except IndexError:
                            print(f'IndexError {IndexError}')

                        # TODO add your specific field formatting here
                        confidence = key['value'][0]['confidence']

                        fieldcount += 1

                        if anchor_key == 'InvoiceNumber':
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

                        gt_key_value = str(dfGTRow.iloc[0][anchor_key]).lower().strip()

                        # Ground Truth value post processing.
                        gt_key_value = str(gt_key_value)

                        if anchor_key_value == gt_key_value:
                            field_match_count += 1

                        print(f'{input_file_name} {anchor_key} GT {gt_key_value} read: {anchor_key_value}')

                        actual_accuracy = field_match_count / fieldcount

                        keys = build_keys_json_object(keys, input_file_name,
                                                      anchor_key, gt_key_value,
                                                      anchor_key_value.strip(),
                                                      confidence,
                                                      issuer_name,
                                                      actual_accuracy)

        except Exception as e:
            exc_type, _, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(f'Predict Error {e} {exc_type} {fname} {exc_tb.tb_lineno}')

    return keys


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
        Read from the .env file
    """
    ANALYZE_END_POINT = os.environ.get("ANALYZE_END_POINT")  # OCR endpoint
    SUBSCRIPTION_KEY = os.environ.get("SUBSCRIPTION_KEY")  # CogSvc key
    STORAGE_ACCOUNT_NAME = os.environ.get("STORAGE_ACCOUNT_NAME")  # Account name for storage
    STORAGE_KEY = os.environ.get("STORAGE_KEY")  # The key for the storage account
    KEY_FIELD_NAMES = os.environ.get("KEY_FIELD_NAMES")  # The fields to be extracted e.g. invoicenumber,date,total
    SAS_PREFIX = os.environ.get("SAS_PREFIX")  # First part of storage account
    SAS = os.environ.get("SAS")  # SAS for storage
    RUN_FOR_SINGLE_ISSUER = os.environ.get("RUN_FOR_SINGLE_ISSUER")  # If true process only this issuer
    DOC_EXT = os.environ.get("DOC_EXT")  # Extension for documents to process
    LANGUAGE_CODE = os.environ.get("LANGUAGE_CODE")  # The language we invoke Read OCR in only en supported now
    GROUND_TRUTH_PATH = os.environ.get("GROUND_TRUTH_PATH")  # This is the path to our Ground Truth
    LOCAL_WORKING_DIR = os.environ.get(
        "LOCAL_WORKING_DIR")  # The local temporary directory to which we write and remove
    CONTAINER_SUFFIX = os.environ.get(
        "CONTAINER_SUFFIX")  # The suffix name of the containers that store the training datasets
    LIMIT_TRAINING_SET = os.environ.get("LIMIT_TRAINING_SET")  # For testing models by file qty trained on
    COUNTRY_CODE = os.environ.get("COUNTRY_CODE")  # Our country code UK/CH
    UNSUPERVISED_ANALYZE_END_POINT = os.environ.get("UNSUPERVISED_ANALYZE_END_POINT")  # Endpoint unsupervised
    SYNONYM_FILE = os.environ.get("SYNONYM_FILE")  # Taxonomy file
    MODEL_LOOKUP = os.environ.get("MODEL_LOOKUP")  # Issuer to modelId lookup file
    MODEL_ID = os.environ.get("MODEL_ID")  # Run for a single modelId
    USE_UNSUPERVISED = os.environ.get("USE_UNSUPERVISED")  # Run in unsupervised mode
    ANCHOR_KEYS = int(os.environ.get("ANCHOR_KEYS"))  # The fields we want to extract
    SAMPLE_NUMBER = int(os.environ.get("SAMPLE_NUMBER"))  # Sample number of files for prediction


def main():
    """
    :param argv: See input args below
    :return: Generates cluster file
    """

    rf = Config.LOCAL_WORKING_DIR
    print(Config.COUNTRY_CODE)
    print('Downloading GT and models')
    print(Config.ADLS_ACCOUNT_NAME)
    print(Config.ADLS_TENANT_ID)
    print(Config.SYNONYM_FILE)

    # TODO Get the ground truth file for the key value extraction
    ground_truth_df, models_df, synonyms = get_ground_truth()

    block_blob_service = BlockBlobService(
        account_name=Config.STORAGE_ACCOUNT_NAME, account_key=Config.STORAGE_KEY)

    issuer_name = ''
    containers = block_blob_service.list_containers()
    for container in containers:
        keys = {}
        # This is where you control what it predicts - container
        if len(Config.RUN_FOR_SINGLE_ISSUER) > 0:
            if (Config.RUN_FOR_SINGLE_ISSUER + Config.CONTAINER_SUFFIX not in container.name) \
                    or container.name[:1] != Config.COUNTRY_VENDOR_PREFIX:
                continue

        # TODO change this if not reflective of the unique identifier
        issuer_name = container.name[:9]

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

        # Create training files for all input files

        if str(Config.USE_UNSUPERVISED) == 'True':
            keys = process_folder_and_predict_unsupervised(keys,
                                                           vendor_folder_path,
                                                           Config.DOC_EXT,
                                                           Config.LANGUAGE_CODE,
                                                           ground_truth_df,
                                                           block_blob_service,
                                                           container.name,
                                                           model_id,
                                                           issuer_name,
                                                           synonyms)

        # Let's clean up to save space
        shutil.rmtree(vendor_folder_path)
        print(f'Predict finished')

        # Let's write our prediction file here
        # TODO add versioning here
        with open(Config.LOCAL_WORKING_DIR + '/unsupervised_predict_' + str(issuer_name) +
                  '_.json', 'w') as json_file:
            json.dump(keys, json_file)
            print('Wrote lookup file', str(issuer_name))


if __name__ == "__main__":
    main()
