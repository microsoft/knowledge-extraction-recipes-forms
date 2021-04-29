# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Utility functions for invoking and querying form custom
form recognizer model
"""

import json
import time
import os
from typing import Dict, List
import requests
from requests.exceptions import RequestException
from tqdm import tqdm


def extract_metadata(form_results: Dict) -> Dict:

    """
    Function that serves as helper to save extracted results from OCR

    to a csv file

    Parameters
    ----------
    form_results: Dict
        (Results from form recognizer)

    Returns
    -------
    Dict
        Object containing extracted items
    """

    if form_results is not None:
        docs = "documentResults"
        fields = form_results["analyzeResult"][docs][0]["fields"]
        text_items = dict()

        for item in fields:
            metadata = fields[item]
            if metadata is not None:
                text_items[item] = metadata["text"]
            else:
                text_items[item] = ""

        return text_items
    return {}


def extract_text_items(metadata: List[Dict], labels: List) -> List:

    """
    Function that extracts text items from
    form recognizer results

    Parameters
    ----------
    metadata: Array
        (metadata from form recognizer results)
    labels: Array
        (List of labels we want to extract from
         form recognizer metadata results)

    Returns
    -------
    Array
        Object containing extracted items
    """
    text_items = []
    for element in tqdm(metadata):
        items = dict()
        meta_dict = element["metadata"]
        if meta_dict is not None and bool(meta_dict) is True:

            if "filename" in element:
                items["filename"] = element["filename"]

            for label in labels:
                if label in element["metadata"]:
                    items[label] = element["metadata"][label]
            text_items.append(items)
    return text_items


def infer_type(input_file: str) -> str:

    """
    Function that infers the type/format of an
    input file

    to a csv file

    Parameters
    ----------
    input_file: String
        (Path to file that will be interpreted)

    Returns
    -------
    String
        The format of the input file
    """

    _, file_extension = os.path.splitext(input_file)
    if file_extension == '':
        print('File extension could not be inferred from inputfile.')
        return ''
    if file_extension == '.pdf':
        return 'application/pdf'
    if file_extension == '.jpeg':
        return 'image/jpeg'
    if file_extension == '.png':
        return 'image/png'
    if file_extension == '.tiff':
        return 'image/tiff'
    print('File extension ' + file_extension + ' not supported')
    return ''


def feed_into_custom_model(endpoint: str,
                           apim_key: str,
                           model_id: str,
                           input_file: str) -> str:

    """
    Function that takes a path to an image file,
    reads in the image as a bytes array, before feeding as
    input to custom form recognizer model

    Parameters
    ----------
    endpoint: String
        (Endpoint to form recognizer resource)
    apim_key: String
        (API key for form recognizer resource)
    model_id: String
        (ID of custom model)
    input_file: String
        (Path to input image/file)

    Raises
    ------
    FileNotFoundError
        If the File is not found
    Exception
        If the response status in not 200

    Returns
    -------
    String
        URL pointing to results from form recognizer
    """

    cstm_endpoint = "/formrecognizer/v2.0/custom/models/%s/analyze" % model_id
    post_url = endpoint + cstm_endpoint
    file_type = infer_type(input_file)
    get_url = ""

    try:
        data_bytes = open(input_file, "rb").read()
    except FileNotFoundError as err_msg:
        raise Exception from err_msg

    params = {
        "includeTextDetails": True
    }

    headers = {
        # Request headers
        'Content-Type': file_type,
        'Ocp-Apim-Subscription-Key': apim_key,
    }

    print('Initiating analysis...')
    resp = requests.post(url=post_url, data=data_bytes,
                         headers=headers, params=params)
    if resp.status_code != 202:
        print("POST analyze failed:\n%s" % json.dumps(resp.json()))
        get_url = resp.json()

    if resp.status_code == 202:
        print("POST analyze succeeded:\n%s" % resp.headers)
        get_url = resp.headers["operation-location"]

    return get_url


def query_results(get_url: str,
                  apim_key: str) -> Dict:

    """
    Function that queries results from form recognizer
    given a GET URL

    Parameters
    ----------
    get_url: String
        (Endpoint pointing to form recognizer results for
         a partcular file/image)
    apim_key: String
        (API key for form recognizer resource)

    Raises
    ------
    RequestException
        If there is an error processing the request
    Exception
        If the response status in not 200

    Returns
    -------
    Dict
        Object containing results from form recognizer
    """

    n_tries = 15
    n_try = 0
    wait_sec = 5
    max_wait_sec = 60
    print('\n Getting analysis results...')

    while n_try < n_tries:
        try:
            headers = {"Ocp-Apim-Subscription-Key": apim_key}
            resp = requests.get(url=get_url, headers=headers)
            resp_json = resp.json()
            if resp.status_code != 200:
                print("GET analyze result failed:\n%s" % json.dumps(resp_json))
                return resp_json

            status = resp_json["status"]
            if status == "succeeded":
                print("Analysis succeeded")
                return resp_json

            if status == "failed":
                print("Analysis failed:\n%s" % json.dumps(resp_json))
                return resp_json

            # Analysis still running. Wait and retry.
            time.sleep(wait_sec)
            n_try += 1
            wait_sec = min(2 * wait_sec, max_wait_sec)

        except RequestException as err_msg:
            raise Exception from err_msg


def run_analysis(endpoint: str,
                 apim_key: str,
                 model_id: str,
                 input_file: str) -> Dict:

    """
    Function that takes a path to an image file,
    before feeding as input to custom form recognizer model

    Parameters
    ----------
    endpoint: String
        (Endpoint to form recognizer resource)
    apim_key: String
        (API key for form recognizer resource)
    model_id: String
        (ID of custom model)
    input_file: String
        (Path to input image/file)

    Raises
    ------
    FileNotFoundError
        If the File is not found
    RequestException
        If there is an error processing the request
    Exception
        If the response status in not 200

    Returns
    -------
    Dict
        Object containing results from form recognizer
    """
    # invoke functions to feed image and query results from model
    try:
        get_url = feed_into_custom_model(endpoint, apim_key, model_id, input_file)
        results = query_results(get_url, apim_key)
        return results
    except (FileNotFoundError, RequestException) as err_msg:
        raise Exception from err_msg
