import json
import os
import shutil
import sys
import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from azure.datalake.store import core, lib
from azure.storage.blob import (
    BlockBlobService,
    ContainerPermissions
)
from dotenv import load_dotenv
from requests import get, post

sys.path.insert(1, '../../common/')
from common.common import find_anchor_keys_in_form

load_dotenv()


def load_json_file(file_path):
    """

    :param file_path: path to file
    :return: The json loaded
    """
    with open(file_path) as json_file:
        data = json.load(json_file)
    return data


def save_json(data, output_file_path):
    """

    :param data: To data to write
    :param output_file_path: The path to write
    :return: Nothing
    """
    with open(output_file_path, 'w') as out_file:
        json.dump(data, out_file, indent=4)


def get_label_file_template(doc_name):
    """
    VOTT header file version
    :param doc_name: Label.json
    :return: The header for the label.json file
    """
    return {
        "document": doc_name,
        "labels": []
    }


def get_field_template(field_name):
    """

    :param field_name: Key identified and labelled
    :return:
    """
    return {
        "label": field_name,
        "key": None,
        # "value": field_value,
        # "values": field_values,
        "value": []
    }


def get_region(page_number, polygon, text):
    """

    :param page_number: OCR page number
    :param polygon: The VOTT polygon value for the field
    :return: The populated json attributes
    """
    bounding_boxes = []
    bounding_boxes.append(polygon)
    return {
        "page": page_number,
        "text": text,
        "boundingBoxes": bounding_boxes
    }


def create_fields_json_file(key_fields):
    """
    This creates the fields.json file used by the labelling tool
    TODO Needs type values added
    :param key_fields: Our key fields from the config
    :return: The json object
    """
    fields = []

    for key_field in key_fields:
        field_value = {'fieldKey': key_field, 'fieldType': "string", 'fieldFormat': "not-specified"}
        fields.append(field_value)

    return {
        "fields": fields
    }


def convert_bbox_to_polygon(bounding_box, width, height):
    """
    Here we map Azure OCR bounding box to VOTT polygon
    returns each coordinate as a percentage of the page size
    :param bounding_box: assumes format list: [x,y,x1,y1,x2,y2, ...]
    :param width: page width
    :param height: page height
    """
    bounding_box = np.array(bounding_box)
    bounding_box[::2] /= width  # Skip every second
    bounding_box[1::2] /= height
    return bounding_box.tolist()


def get_key_field_data(key_field, key_field_details):
    """
    This checks to see which key fields we have extracted. Totals fields are typically
    multi-page so we want to find them on the last page ideally
    :param key_field: The key of the field extracted
    :param key_field_details: The keys identified object
    :return: The coordinates of the field identified
    """
    multi_page_fields = Config.MULTI_PAGE_FIELDS.split()
    location = None

    for field in key_field_details:
        if (key_field in multi_page_fields) and (key_field in field):
            # We need the last one
            location = field
        else:  # Return the first one
            if key_field in field:
                location = field
                return location

    return location


def create_label_file(file_name, key_fields, key_field_details):
    """
    :param file_name: document file probably a PDF or TIF
    :param key_fields: the fields to extract from the OCR
    :param key_field_details: the extracted values extracted from the OCR
    """
    # create label file
    label_file = get_label_file_template(file_name)
    keys = {}

    if Config.MULTI_PAGE_FIELDS is not None:
        multi_page_fields = Config.MULTI_PAGE_FIELDS.split(',')
    else:
        multi_page_fields = ''

    # Let's get the number of unique fields extracted
    fields_extracted = []
    unique_fields_extracted = 0

    # Initialise and Build
    for key_field in key_fields:
        key_field = key_field.strip()
        for field in key_field_details:
            if key_field.strip() in field:
                if key_field in keys:
                    keys[key_field].append(field)
                else:
                    keys[key_field] = []
                    keys[key_field].append(field)

    # Here is some example logic to ensure we don't have overlapping values, this can happen when
    # a net value is the same as a Total for example
    if ('NetValue' in keys) and ('TotalAmount' in keys):
        if keys['NetValue'][-1]['BoundingBox'] == keys['TotalAmount'][-1]['BoundingBox']:
            print('Removing overlapping net value', file_name)
            net_value = keys['NetValue'][-1]
            keys['NetValue'].remove(net_value)

    field_detail = None

    # Add key field values to the label file
    for key_field, _ in keys.items():
        key_field = key_field.strip()
        fields_extracted.append(key_field)

        # Take the last value for multi-page - totals values are best taken from the end of the last
        # page
        try:
            if (key_field in multi_page_fields) and (key_field in keys):
                field_detail = keys[key_field][-1]
            elif key_field in keys:
                field_detail = keys[key_field][0]
            print('field_detail', key_field, field_detail)
        except IndexError:
            print('Index error', key_field, field_detail)
            continue

        if field_detail is None:
            continue

        page = field_detail['page']
        width = field_detail['width']
        height = field_detail['height']
        field_bounding_box = field_detail['BoundingBox']
        field_value = field_detail[key_field]

        field_values = [field_value]  # if more than one bounding box.
        field = get_field_template(key_field)

        # Convert to percentage coordinates
        polygon = convert_bbox_to_polygon(field_bounding_box, float(width), float(height))

        region = get_region(page, polygon, field_value)

        # Add the key region to the field
        field['value'].append(region)

        # Add the field to the doc template - each field is a 'label'
        label_file['labels'].append(field)

        # Now we determine unique fields extracted
        unique_fields_extracted = len(set(fields_extracted))

    return label_file, unique_fields_extracted


def form_recognizerv2_train(region, subscription_key, training_data_blob_sas_url, prefix=None,
                            includeSubFolders=False,
                            useLabelFile=True):
    """
    Simple rest call to FR V2
    :param base_url: The prefix of the full url
    :param subscription_key: CogSvc key
    :param training_data_blob_sas_url: SAS URL for storage containing training set
    :param prefix: The account name suffix e.g, https://[account].blob.core.windows.net
    :param includeSubFolders: True/False
    :param useLabelFile: Train with labels for Supervised - Always true
    :return: The modelId and accuracy etc
    """

    """Trains a document with the Form Recognizer supervised model """

    headers = {
        # Request headers
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": subscription_key,
    }
    url = f"https://{region}.api.cognitive.microsoft.com/formrecognizer/v2.0-preview/custom/models"

    print('url', url)
    print('subscription_key', subscription_key)
    print('training_data_blob_sas_url', training_data_blob_sas_url)

    body = {
        "source": training_data_blob_sas_url,
        "sourceFilter": {
            "prefix": prefix,
            "includeSubFolders": includeSubFolders
        },
        "useLabelFile": useLabelFile}

    try:
        resp = post(url=url, json=body, headers=headers)

        if resp.status_code == 201:
            status_url = resp.headers['Location']
            print(f"Model analyse submitted. Operation Location: {status_url}")
            headers = {"Ocp-Apim-Subscription-Key": subscription_key}
            resp = get(url=status_url, headers=headers)
            count = 0
            max_retry = 500
            while (count < max_retry and resp.status_code == 200 and (
                    resp.json()['modelInfo']['status'] == 'running' or resp.json()['modelInfo'][
                'status'] == 'creating')):
                resp = get(url=status_url, headers=headers)
                time.sleep(0.5)
                count += 1
            return resp.json()
        else:
            print(f"Error training: {str(resp.text)}")
    except Exception as e:
        print(f"Error training model : {e}")

    return None


def call_ocr(file_path, file_name, language_code, region, subscription_key):
    """
    Let's only call OCR if we need to
    :param file_path: Path to file to OCR
    :param file_name: File name to OCR
    :return: The json response of the OCR
    """

    headers = {
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Content-Type": "application/pdf"
    }

    with open(os.path.join(file_path, file_name), 'rb') as ocr_file:
        file_content = ocr_file.read()

    operation_location = ""
    print(f"Analyzing file {file_name}...")
    analyze_result_response = None

    try:
        url = f"https://{region}.api.cognitive.microsoft.com/formrecognizer/v2.0-preview/layout/analyze"
        print(url)
        resp = post(url=url, data=file_content, headers=headers)
        print(resp, resp.status_code, resp.text)
        operation_location = resp.headers['Operation-Location']
        print(f"Analyze Operation Location: {operation_location}")
    except Exception as e:
        print(f"Error analyzing file: {e}")

    # Getting response result
    if (operation_location != ""):
        resp_analyze = get(url=operation_location, headers=headers)
        analyze_result_response = resp_analyze.json()
        print(analyze_result_response)
        count = 0
        max_retry = 30
        try:
            while (count < max_retry and resp_analyze.status_code == 200 and (
                    analyze_result_response['status'] == 'running' or analyze_result_response[
                'status'] == 'notStarted')):
                resp_analyze = get(url=operation_location, headers=headers)
                analyze_result_response = resp_analyze.json()
                time.sleep(0.5)
                count += 1
            print(f"File {file_name} status: {analyze_result_response['status']}")
        except Exception as e:
            print(f"Error analyzing file: {e}")

    return analyze_result_response


def create_training_files_for_document(
        file_name,
        key_field_names,
        ground_truth_df,
        ocr_data,
        pass_number):
    """
    Create the ocr.json file and the label file for a document
    :param file_path: location of the document
    :param file_name: just the document name.ext
    :param key_field_names: names of the key fields to extract
    :param ocr_data: Previously OCR form
    :param pass_number: Are we processing word level or both word and line level
    """

    extraction_file_name = file_name[:-4] + '.ocr.json'
    # Now we go and reverse search the form for the Ground Truth values
    key_field_data = find_anchor_keys_in_form(
        df_gt=ground_truth_df,
        filename=extraction_file_name,
        data=ocr_data,
        anchor_keys=key_field_names,
        pass_number=pass_number)

    print(f"key_field_data {len(key_field_data)} {key_field_data} {file_name}")

    label_file, unique_fields_extracted = create_label_file(
        file_name,
        key_field_names,
        key_field_data[extraction_file_name]
    )

    return ocr_data, label_file, unique_fields_extracted


def select_best_training_set(pass_level, vendor_folder_path_pass1, vendor_folder_path_pass2, min_labelled_data):
    """
    This function will select and cleanup the best training set
    :param pass_level: The object containing our autolabelled training set
    :param vendor_folder_path_pass1: First pass folder
    :param vendor_folder_path_pass2: Second pass folder
    :return: The best training set
    """
    # Now we need to train our two pass models and select the best model
    # We know that the highest amount of correctly labelled fields will
    # Yield the best accuracy
    pass1_max = 0
    pass2_max = 0
    pass1_sum = 0
    pass2_sum = 0

    # Now we get the max field count and average retrieved from the sampled training set
    for level, file_values in pass_level.items():
        for file_value in file_values:
            for i, key_count in enumerate(file_value):
                if int(level) == 1:
                    pass1_sum += int(key_count[1])
                    if int(key_count[1]) > pass1_max:
                        pass1_max = key_count[1]
                else:
                    pass2_sum += int(key_count[1])
                    if int(key_count[1]) > pass2_max:
                        pass2_max = key_count[1]

    print(f"Pass 1 max: {pass1_max} sum {pass1_sum / (i + 1)}")
    print(f"Pass 2 max: {pass2_max} sum {pass2_sum / (i + 1)}")

    # Now we check whether we have enough to train a model - 5 minimum and remove the files
    # not optimum to our training set. We will check for maximum fields present, if this is
    # not possible we will take the next best set max - 1
    reduce_max = 0

    pass1_count, pass2_count, pass1_sum, pass2_sum = \
        build_valid_training_set(pass_level, pass1_max, pass2_max, reduce_max)

    if (pass1_count < min_labelled_data) and (pass2_count < min_labelled_data):
        print(f"Reducing max fields due to insufficient well labelled samples")
        reduce_max = 1
        pass1_count, pass2_count, pass1_sum, pass2_sum = \
            build_valid_training_set(pass_level, pass1_max, pass2_max, reduce_max)

        print(f"Pass 1 max: {pass1_max - reduce_max} sum {pass1_sum / (i + 1)}")
        print(f"Pass 2 max: {pass2_max - reduce_max} sum {pass2_sum / (i + 1)}")

    print(f"Pass 1 count: {pass1_count}")
    print(f"Pass 2 count: {pass2_count}")

    selected_training_set = None

    # Find the training set with the best labelled fields
    if pass1_max > pass2_max:
        # This is the minimum we need to train a model
        if pass1_count >= min_labelled_data:
            selected_training_set = vendor_folder_path_pass1
        else:
            print(f"Not enough well labelled files in dataset {vendor_folder_path_pass1}")
    elif pass2_max > pass1_max:
        # This is the minimum we need to train a model
        if pass2_count >= min_labelled_data:
            selected_training_set = vendor_folder_path_pass2
        else:
            print(f"Not enough well labelled files in dataset {vendor_folder_path_pass2}")
    elif pass1_max == pass2_max:
        if pass1_count > pass2_count:
            # This is the minimum we need to train a model
            if pass1_count >= min_labelled_data:
                selected_training_set = vendor_folder_path_pass1
            else:
                print(f"Not enough well labelled files in dataset {vendor_folder_path_pass1}")
        else:
            # This is the minimum we need to train a model
            if pass2_count >= min_labelled_data:
                selected_training_set = vendor_folder_path_pass2
            else:
                print(f"Not enough well labelled files in dataset {vendor_folder_path_pass2}")

    if selected_training_set is not None:
        # Let's optimise the training set by removing the badly labelled items
        cleanup_training_set(pass_level, pass1_max, pass2_max,
                             vendor_folder_path_pass1, vendor_folder_path_pass2, reduce_max)
    else:
        # We need to take the best partially labelled dataset
        if pass1_count > pass2_count:
            selected_training_set = vendor_folder_path_pass1
        else:
            selected_training_set = vendor_folder_path_pass2

    return selected_training_set


def process_folder(
        vendor_folder_path_pass1,
        vendor_folder_path_pass2,
        key_field_names,
        ext,
        language_code,
        ground_truth_df,
        blob_service,
        container_name,
        region,
        subscription_key
):
    """
    Iterate through our storage accounts, download,correlate with Ground Truth and invoke downstream
    functions


    :param vendor_folder_path_pass1: First pass folder
    :param vendor_folder_path_pass2: Second pass folder
    :param key_field_names: The key fields we want to extract
    :param ext: File extensions
    :param language_code: Language code for OCR - always english for now
    :param ground_truth_df: Our Ground Truth data frame
    :param blob_service: The Blob Service object
    :param container_name: The storage blob container that we are processing
    :param region: The region the Cognitive Services are deployed
    :param subscription_key: The subscription key for the cognitive services
    :return: A dictionary object containing lists of filenames for OCR and labels generated for the pass level
    """

    blob_names = blob_service.list_blobs(container_name)
    for blob in blob_names:
        blob_service.get_blob_to_path(container_name, blob.name, file_path=vendor_folder_path_pass1 + '/' + blob.name)

    input_doc_files = [f for f in os.listdir(vendor_folder_path_pass1) if f.endswith(ext)]

    num_files = len(input_doc_files)
    print(f"Number of files for OCR {len(input_doc_files)} {ext}")

    # This object stores a list of filenames for the original file, the OCR and the label file
    pass_level = {}

    # Counter for number of corresponding Ground Truth files found
    file_ground_truth = 0

    # Now we check if we have OCR files, if not we call OCR
    for input_file_name in input_doc_files:

        # check that we have ground truth for the file
        df_vendor_gt = ground_truth_df[ground_truth_df['FILENAME'] == str(input_file_name[:len(input_file_name) - 4])]
        if len(df_vendor_gt) == 0:
            print(f"No GT record for {str(input_file_name[:len(input_file_name) - 4])}")
            continue
        else:
            print(f"GT Filename {df_vendor_gt['FILENAME'].iloc[0]} {str(input_file_name[:len(input_file_name) - 4])}")

        file_ground_truth += 1

        ocr_file_path = vendor_folder_path_pass1 + '/' + input_file_name + '.ocr.json'
        # Let's check if the file has already been OCR'd
        print(f"Checking for previous OCR {ocr_file_path}")
        ocr_data = None
        if os.path.isfile(ocr_file_path):
            with open(ocr_file_path) as ocr_file:
                ocr_data = json.load(ocr_file)

        if ocr_data is None:
            analyze_layout_ocr = call_ocr(vendor_folder_path_pass1, input_file_name, language_code, region,
                                          subscription_key)
            analyze_layout_ocr_output_file_path = \
                f"{vendor_folder_path_pass1}/{input_file_name}.ocr.json"
            save_json(analyze_layout_ocr, analyze_layout_ocr_output_file_path)

    # Now we copy all OCR'd files to our second pass directory
    if os.path.isdir(vendor_folder_path_pass2):
        shutil.rmtree(vendor_folder_path_pass2)

    # Linux OS
    shutil.copytree(vendor_folder_path_pass1, vendor_folder_path_pass2)
    paths = [vendor_folder_path_pass1, vendor_folder_path_pass2]
    pass_number = 0

    for pass_path in paths:
        # Let's auto-label for pass_path in paths:
        pass_number += 1
        pass_level[pass_number] = []
        output_files = []

        input_doc_files = [f for f in os.listdir(pass_path) if f.endswith(ext)]
        for input_file_name in input_doc_files:
            ocr_file_path = pass_path + '/' + input_file_name + '.ocr.json'

            with open(ocr_file_path) as ocr_file:
                ocr_data = json.load(ocr_file)

            analyze_layout_ocr, label_file, key_length = create_training_files_for_document(
                input_file_name,
                key_field_names,
                ground_truth_df,
                ocr_data,
                pass_number)

            output_files.append([input_file_name, key_length])

            # save files
            label_output_file_path = f"{pass_path}/{input_file_name}.labels.json"
            save_json(label_file, label_output_file_path)

            fields_file = create_fields_json_file(key_field_names)
            fields_output_file_path = f"{pass_path}/fields.json"
            save_json(fields_file, fields_output_file_path)

        # Add to the top level dict data structure
        pass_level[pass_number].append(output_files)

    return pass_level, num_files, file_ground_truth


def upload_blobs_to_container(block_blob_service, input_folder_path, container_name, ext):
    """

    :param block_blob_service: Our blob storage instance
    :param input_folder_path: The folder we are working with
    :param container_name: The blob storage container name
    :param ext: File extension 'pdf'
    :return: Nothing
    """

    print(f"Upload_blobs_to_container {input_folder_path}")
    document_files = [f for f in os.listdir(input_folder_path) if f.endswith(ext)]

    for i, doc_file_name in enumerate(document_files):

        ocr_file_name = doc_file_name + '.ocr.json'
        label_file_name = doc_file_name + '.labels.json'

        doc_file_path = input_folder_path + os.path.sep + doc_file_name
        ocr_file_path = input_folder_path + os.path.sep + ocr_file_name
        label_file_path = input_folder_path + os.path.sep + label_file_name

        try:
            block_blob_service.create_blob_from_path(
                container_name, doc_file_name, doc_file_path)

            block_blob_service.create_blob_from_path(
                container_name, ocr_file_name, ocr_file_path)

            if i > int(Config.LIMIT_TRAINING_SET):
                continue
            else:
                block_blob_service.create_blob_from_path(
                    container_name, label_file_name, label_file_path)

        except Exception as e:
            print(f"Unable to upload blob {doc_file_name} {e}")
            continue


def create_container(block_blob_service, account_name, container_name):
    """
    This function creates the container if it does not exist
    :param block_blob_service: The storage blob service instance
    :param account_name: The storage account name
    :param container_name: The storage container
    :return: The SAS for the container
    """
    if not block_blob_service.exists(container_name):
        block_blob_service.create_container(container_name)

    sas_qs = block_blob_service.generate_container_shared_access_signature(
        container_name,
        ContainerPermissions.READ | ContainerPermissions.LIST,
        expiry=datetime.now() + timedelta(days=1)
    )

    container_sas_url = f"https://{account_name}.blob.core.windows.net/{container_name}?{sas_qs}"

    return container_sas_url, sas_qs


def build_valid_training_set(pass_level, pass1_max, pass2_max, reduce_max):
    """
    We need to evaluate how well the auto-labelling process has worked per pass.
    How many fields have we managed to extract (max) and how many forms in the training set
    have we managed to extract the max for. We will need to decrement if we cannot hit our
    minimum threshold of 10 forms required for training

    :param pass_level: The dict object containing our auto-labelling results
    :param pass1_max: The maximum fields extracted during autolabel pass 1
    :param pass2_max: The maximum fields extracted during autolabel pass 2
    :param reduce_max: We decrement if we cannot find fully labelled forms
    :return: The counts and sums per pass as ints
    """
    pass1_count = 0
    pass2_count = 0
    pass1_sum = 0
    pass2_sum = 0

    for level, file_values in pass_level.items():
        for file_value in file_values:
            for _, key_count in enumerate(file_value):
                if int(level) == 1:
                    pass1_sum += int(key_count[1])
                    if int(key_count[1]) == (pass1_max - reduce_max):
                        pass1_count += 1
                else:
                    pass2_sum += int(key_count[1])
                    if int(key_count[1]) == (pass2_max - reduce_max):
                        pass2_count += 1

    return pass1_count, pass2_count, pass1_sum, pass2_sum


def cleanup_training_set(pass_level, pass1_max, pass2_max,
                         vendor_folder_path_pass1, vendor_folder_path_pass2, reduce_max):
    """

    :param pass_level: The dict object containing our auto-labelling results
    :param pass1_max: The maximum fields extracted during autolabel pass 1
    :param pass2_max: The maximum fields extracted during autolabel pass 2
    :param reduce_max: We decrement if we cannot find fully labelled forms
    :param vendor_folder_path_pass1: The local training directory pass 1
    :param vendor_folder_path_pass2: The local training directory pass 1
    :return: Nothing
    """

    for level, file_values in pass_level.items():
        for file_value in file_values:
            for _, key_count in enumerate(file_value):
                if int(level) == 1:
                    if int(key_count[1]) < (pass1_max - reduce_max):
                        os.remove(vendor_folder_path_pass1 + "/" + key_count[0])
                else:
                    if int(key_count[1]) < (pass2_max - reduce_max):
                        os.remove(vendor_folder_path_pass2 + "/" + key_count[0])


def get_ground_truth_from_adls(adls_account_name, tenant_id, ground_truth_adls_path):
    """

    :param adls_account_name: The data lake store
    :param tenant_id: Azure AD tentant
    :param ground_truth_adls_path: The data lake path to the Ground Truth
    :return: Data frame with the Ground Truth
    """
    df = pd.DataFrame()
    adls_credentials = lib.auth(tenant_id=tenant_id, resource='https://datalake.azure.net/')
    adlsFileSystemClient = core.AzureDLFileSystem(adls_credentials, store_name=adls_account_name)

    with adlsFileSystemClient.open(ground_truth_adls_path, 'rb') as f:
        df = pd.read_pickle(f, compression=None)

    return df


class Config:
    """
    Read from the .env file
    """
    TRAINING_END_POINT = os.environ.get("TRAINING_END_POINT")  # FR Training endpoint
    ANALYZE_END_POINT = os.environ.get("ANALYZE_END_POINT")  # OCR endpoint
    SUBSCRIPTION_KEY = os.environ.get("SUBSCRIPTION_KEY")  # CogSvc key
    STORAGE_ACCOUNT_NAME = os.environ.get("STORAGE_ACCOUNT_NAME")  # Account name for storage
    STORAGE_KEY = os.environ.get("STORAGE_KEY")  # The key for the storage account
    KEY_FIELD_NAMES = os.environ.get("KEY_FIELD_NAMES")  # The fields to be extracted e.g. invoicenumber,date,total
    ADLS_ACCOUNT_NAME = os.environ.get("ADLS_ACCOUNT_NAME")  # Data lake account
    ADLS_TENANT_ID = os.environ.get("ADLS_TENANT_ID")  # Azure AD tenant id
    SAS_PREFIX = os.environ.get("SAS_PREFIX")  # First part of storage account
    SAS = os.environ.get("SAS")  # SAS for storage
    RUN_FOR_SINGLE_ISSUER = os.environ.get("RUN_FOR_SINGLE_ISSUER")  # If true process only this issuer
    MOUNT_DIR = os.environ.get("MOUNT_DIR")  # Model mount directory to which to write training files to
    DOC_EXT = os.environ.get("DOC_EXT")
    LANGUAGE_CODE = os.environ.get("LANGUAGE_CODE")  # The language we invoke Read OCR in only en supported now
    GROUND_TRUTH_PATH = os.environ.get("GROUND_TRUTH_PATH")  # This is the path to our Ground Truth
    LOCAL_WORKING_DIR = os.environ.get(
        "LOCAL_WORKING_DIR")  # The local temporary directory to which we write and remove
    CONTAINER_SUFFIX = os.environ.get(
        "CONTAINER_SUFFIX")  # The suffix name of the containers that store the training datasets
    LIMIT_TRAINING_SET = os.environ.get("LIMIT_TRAINING_SET")  # For testing models by file qty trained on
    TRAIN_TEST = os.environ.get("TRAIN_TEST")  # Suffixes train or test to container name
    MULTI_PAGE_FIELDS = os.environ.get("MULTI_PAGE_FIELDS")  # These fields appear over multiple pages
    # and as such are handled differently. Typically totals fields on an invoice
    REGION = os.environ.get("REGION")  # The region Form Recognizer and OCR are deployed
    MINIMUM_LABELLED_DATA = os.environ.get("MINIMUM_LABELLED_DATA")  # The minimum number of well labelled samples to
    #  train on


def main():
    """

    The entry point - let's download the files from the blob. Find the matching Ground Truth
    record, and sample the files. We then call OCR if needed, reverse search the file for the
    Ground Truth keys we want to extract. We generate two search approaches, pick the best model,
    and then remove all training files that are not optimum. We then train.
    :param argv: All read from the .env file - see function process_folder for
    :return: Generates cluster file

    """

    rf = Config.LOCAL_WORKING_DIR
    sas_prefix = Config.SAS_PREFIX
    sas = Config.SAS

    lst_modelId = []
    lst_vendorId = []
    lst_fieldslen = []
    lst_accuracy = []
    lst_num_files = []
    lst_num_ground_truth = []

    # get the ground truth file for the key value extraction from Azure Data Lake
    ground_truth_df = get_ground_truth_from_adls(
        Config.ADLS_ACCOUNT_NAME,
        Config.ADLS_TENANT_ID,
        Config.GROUND_TRUTH_PATH)

    key_field_names = [f for f in Config.KEY_FIELD_NAMES.split(',')]

    block_blob_service = BlockBlobService(
        account_name=Config.STORAGE_ACCOUNT_NAME, account_key=Config.STORAGE_KEY)

    containers = block_blob_service.list_containers()
    for container in containers:

        if len(Config.RUN_FOR_SINGLE_ISSUER) > 0:
            if (Config.RUN_FOR_SINGLE_ISSUER + Config.CONTAINER_SUFFIX + Config.TRAIN_TEST
                    not in container.name):
                continue

        if Config.CONTAINER_SUFFIX + Config.TRAIN_TEST \
                not in container.name:
            continue

        vendor_folder_path = f"{rf}/{container.name}"
        if not os.path.exists(vendor_folder_path):
            print(f"Creating folder {vendor_folder_path}")
            os.mkdir(vendor_folder_path)

        # Now we create our two pass folders to select the best model
        vendor_folder_path_pass1 = f"{vendor_folder_path}/pass1"
        if not os.path.exists(vendor_folder_path_pass1):
            os.mkdir(vendor_folder_path_pass1)

        vendor_folder_path_pass2 = f"{vendor_folder_path}/pass2"
        print(f"Processing container {container.name}")

        # create training files for all input files
        pass_level, num_files, num_ground_truth = process_folder(
            vendor_folder_path_pass1,
            vendor_folder_path_pass2,
            key_field_names,
            Config.DOC_EXT,
            Config.LANGUAGE_CODE,
            ground_truth_df,
            block_blob_service,
            container.name,
            Config.REGION,
            Config.SUBSCRIPTION_KEY)

        selected_training_set = select_best_training_set(pass_level, vendor_folder_path_pass1, vendor_folder_path_pass2,
                                                         Config.MINIMUM_LABELLED_DATA)

        # Debug data structure
        with open(Config.RUN_FOR_SINGLE_ISSUER + '_pass_level.txt', 'w') as file:
            file.write(json.dumps(pass_level))

        # Upload the best training set to the container
        upload_blobs_to_container(block_blob_service, selected_training_set, container.name, Config.DOC_EXT)
        print(f"Uploaded files to blob {container.name} training set {selected_training_set}")

        # Let's clean up - Linux
        shutil.rmtree(vendor_folder_path_pass1)
        shutil.rmtree(vendor_folder_path_pass2)

        # Train the model on the optimised dataset
        sasurl = sas_prefix + container.name + sas
        train_response = form_recognizerv2_train(Config.REGION,
                                                 Config.SUBSCRIPTION_KEY,
                                                 sasurl)
        print(f"Trained {train_response}")

        modelId = 'None'
        fieldlen = 0
        accuracy = 0

        try:

            modelId = train_response['modelInfo']['modelId']
            fieldlen = len(train_response['trainResult']['trainingFields']['fields'])
            accuracy = train_response['trainResult']['averageModelAccuracy']

            print(train_response['trainResult']['modelId'])
            lst_vendorId.append(container.name[:9])
            lst_modelId.append(train_response['trainResult']['modelId'])
            lst_fieldslen.append(fieldlen)
            lst_accuracy.append(accuracy)
            lst_num_files.append(num_files)
            lst_num_ground_truth.append(num_ground_truth)

        except Exception as e:
            print(f"Training error {e}")
            lst_vendorId.append(container.name[:9])
            lst_modelId.append(modelId)
            lst_fieldslen.append(fieldlen)
            lst_accuracy.append(accuracy)
            lst_num_files.append(num_files)
            lst_num_ground_truth.append(num_ground_truth)

        with open("./" + container.name[:9] +
                  Config.CONTAINER_SUFFIX + ".txt", "a+") as autolabel:
            autolabel.write("\n" + container.name[:9] + "," + modelId + "," +
                            str(fieldlen) + "," + str(accuracy) + "," +
                            str(num_files) + "," + str(num_ground_truth))
        print(f"Updated ./ {container.name[:9] + Config.CONTAINER_SUFFIX} .csv")

    data = {'vendorId': lst_vendorId, 'modelId': lst_modelId,
            'fieldNumber': lst_fieldslen, 'accuracy': lst_accuracy,
            'numFiles': lst_num_files, 'numFilesInGroundTruth': lst_num_ground_truth}
    df_lookup = pd.DataFrame(data)
    autolabel_pdf = rf + "/" + Config.CONTAINER_SUFFIX + ".csv"
    df_lookup.to_csv(autolabel_pdf, sep=',')
    print(f"Wrote lookup file {autolabel_pdf}")


if __name__ == "__main__":
    main()
