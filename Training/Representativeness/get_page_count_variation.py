#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json
import os
import shutil
from datetime import datetime, timedelta

from azure.storage.blob import (
    BlockBlobService,
    ContainerPermissions
)
from dotenv import load_dotenv
from requests import Session

load_dotenv()


def load_json_file(file_path):
    """

    :param file_path: Path to the json file
    :return: The loaded json object
    """
    with open(file_path) as json_file:
        data = json.load(json_file)
    return data


def save_json(data, output_file_path):
    """

    :param data: The json data to save
    :param output_file_path: The path to save to
    :return: None
    """
    with open(output_file_path, 'w') as out_file:
        json.dump(data, out_file, indent=4)


def find_number_of_pages_in_invoice(filename, data):
    """
    This function will simply return the number of pages in the document OCR

    :param filename: The name of the file that we are processing
    :param data: The OCR for the record in question
    :return: A json object with the fields and corresponding bounding boxes
    """
    print('Checking page count', filename)
    return len(data['analyzeResult']['readResults'])


def check_page_numbers_for_document(
        file_path,
        file_name,
        language_code,
        ocr_data):
    """
    Create the ocr.json file and the label file for a document
    :param file_path: location of the document
    :param file_name: just the document name.ext
    :param language_code: The language code for the OCR service
    :param ocr_data: Previously OCR form
    """

    print(f'Checking OCR file')
    analyze_result_response = None
    session = Session()
    page_count = 0

    if ocr_data is None:

        headers = {
            "Ocp-Apim-Subscription-Key": Config.SUBSCRIPTION_KEY
        }

        try:
            url = Config.ANALYZE_END_POINT + \
                  '/formrecognizer/v2.0/readLayout/analyze?language=' + language_code.lower() + \
                  '&mode=docMode'
            print('Calling OCR', file_path, file_name, url)
            files = {'file': (file_name, open(file_path, 'rb'), 'application/pdf', {'Expires': '0'})}
            resp = session.post(url=url, files=files, headers=headers)
            analyze_result_response = resp.json()

        except Exception as e:
            print(f'Exception readLayout {e}')
    else:
        print(f'OCR record loaded')
        analyze_result_response = ocr_data

    extraction_file_name = file_name + '.ocr.json'

    if analyze_result_response is not None:
        page_count = find_number_of_pages_in_invoice(
            extraction_file_name,
            analyze_result_response)

    return page_count, analyze_result_response


def process_folder(
        output_files,
        input_folder_path,
        ext,
        language_code,
        blob_service,
        container_name):
    """
    Iterate through containers and download locally to parse and test
    :param output_files: The path to write the output files to
    :param input_folder_path: The local path to process
    :param ext: The extension of the forms to process e.g. pdf
    :param language_code: The language code for OCR e.g. en
    :param blob_service: Our instantiated blob service object
    :param container_name: The storage container we are processing
    :return: The output files
    """
    blob_names = blob_service.list_blobs(container_name)
    for blob in blob_names:
        blob_service.get_blob_to_path(container_name, blob.name, file_path=input_folder_path + '/' + blob.name)

    input_doc_files = [f for f in os.listdir(input_folder_path) if f.endswith(ext)]

    # num_files = len(input_doc_files)
    print(f'Number of files for OCR {len(input_doc_files)} {ext}')

    number_of_multipages = 0

    for input_file_name in input_doc_files:

        ocr_file_path = input_folder_path + '/' + input_file_name + '.ocr.json'
        # Let's check if the file has already been OCR'd
        print(f'Checking for previous OCR {ocr_file_path}')
        ocr_data = None
        if os.path.isfile(ocr_file_path):
            with open(ocr_file_path) as ocr_file:
                ocr_data = json.load(ocr_file)
                print(f'Loaded existing OCR {ocr_file_path}')

        page_count, analyze_result_ocr = check_page_numbers_for_document(
            f"{input_folder_path}/{input_file_name}",
            input_file_name,
            language_code,
            ocr_data
        )

        if int(page_count) > 1:
            number_of_multipages += 1

        # save files
        analyze_layout_ocr_output_file_path = f"{input_folder_path}/{input_file_name}.ocr.json"
        save_json(analyze_result_ocr, analyze_layout_ocr_output_file_path)

    output_files = build_dataset_attributes_json_object(output_files, container_name,
                                                        len(input_doc_files),
                                                        number_of_multipages,
                                                        (number_of_multipages / len(input_doc_files)) * 100)

    return output_files


def upload_blobs_to_container(block_blob_service, input_folder_path, container_name, ext):
    """

    :param block_blob_service: The instantiated blob service object
    :param input_folder_path: The local folder we are processing
    :param container_name: The name of the storage container
    :param ext: The extension of the forms to process e.g. pdf
    :return: None
    """
    print(f'Upload_blobs_to_container {input_folder_path}')
    document_files = [f for f in os.listdir(input_folder_path) if f.endswith(ext)]

    for doc_file_name in document_files:

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

            block_blob_service.create_blob_from_path(
                container_name, label_file_name, label_file_path)

        except Exception as e:
            print(f'Unable to upload blob {doc_file_name} {e}')
            continue


def create_container(block_blob_service, account_name, container_name):
    """
    Create the storage container if it does nor exist
    :param block_blob_service: The instantiated blob service object
    :param account_name: The storage account name
    :param container_name: The storage container
    :return: The sas key
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


def build_dataset_attributes_json_object(output_files, container_name, num_files, num_multi_page,
                                         percentage_multi_page):
    """

    :param output_files: The files to output
    :param container_name: The storage container name
    :param num_files: The number of files processed
    :param num_multi_page: The number of multi-page forms
    :param percentage_multi_page: The % of forms that are multi-page
    :return: The output files object
    """
    output_files[container_name].append({
        'numberInvoices': num_files,
        'numMultipage': num_multi_page,
        'percentageMultipage': percentage_multi_page
    })

    return output_files


class Config:
    """
    Loaded from .env file
    """
    TRAINING_END_POINT = os.environ.get("TRAINING_END_POINT")
    ANALYZE_END_POINT = os.environ.get("ANALYZE_END_POINT")
    SUBSCRIPTION_KEY = os.environ.get("SUBSCRIPTION_KEY")
    STORAGE_ACCOUNT_NAME = os.environ.get("STORAGE_ACCOUNT_NAME")
    STORAGE_KEY = os.environ.get("STORAGE_KEY")
    KEY_FIELD_NAMES = os.environ.get("KEY_FIELD_NAMES")
    SAS_PREFIX = os.environ.get("SAS_PREFIX")
    SAS = os.environ.get("SAS")
    RUN_FOR_SINGLE_VENDOR = os.environ.get("RUN_FOR_SINGLE_VENDOR")
    LOCAL_WORKING_DIR = os.environ.get("LOCAL_WORKING_DIR")
    DOC_EXT = os.environ.get("DOC_EXT")
    LANGUAGE_CODE = os.environ.get("LANGUAGE_CODE")
    CONTAINER_SUFFIX = os.environ.get(
        "CONTAINER_SUFFIX")  # The suffix name of the containers that store the training datasets


def main():
    """
    :param: See Config class which reads from .env file
    :return: Generates cluster file
    """

    rf = Config.LOCAL_WORKING_DIR

    block_blob_service = BlockBlobService(
        account_name=Config.STORAGE_ACCOUNT_NAME, account_key=Config.STORAGE_KEY)

    output_files = {}

    containers = block_blob_service.list_containers()
    for container in containers:

        if len(Config.RUN_FOR_SINGLE_VENDOR) > 0:
            if Config.RUN_FOR_SINGLE_VENDOR + Config.CONTAINER_SUFFIX not in container.name:
                continue
        elif Config.CONTAINER_SUFFIX not in container.name:
            continue

        output_files[container.name] = []

        vendor_folder_path = f"{rf}/{container.name}"
        if not os.path.exists(vendor_folder_path):
            print(f'Creating folder {vendor_folder_path}')
            os.mkdir(vendor_folder_path)

        print(f'Processing {container.name}')

        # create training files for all input files
        output_files = process_folder(
            output_files,
            vendor_folder_path,
            Config.DOC_EXT,
            Config.LANGUAGE_CODE,
            block_blob_service,
            container.name)

        # upload to container
        upload_blobs_to_container(block_blob_service, vendor_folder_path, container.name, Config.DOC_EXT)
        print(f'Uploaded files to blob {container.name}')
        shutil.rmtree(vendor_folder_path)
        print(f'Removing {vendor_folder_path}')

    with open("./page_count_validation.json", "a+") as pagecountfile:
        pagecountfile.write(json.dumps(output_files))

        print(f'Updated ./ {container.name[:9]} -page_count_validation.json')

    print(f'Wrote lookup file')


if __name__ == "__main__":
    main()
