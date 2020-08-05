#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging
from requests import get, post
import time

from . import utils
from . import formatting


def train_model(region, subscription_key, training_data_blob_sas_url, doctype, use_label_file=True):

    """Trains a document with the Form Recognizer supervised model"""

    headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": subscription_key,
    }
    url = f"https://{region}.api.cognitive.microsoft.com/formrecognizer/v2.0/custom/models"
    prefix = f"{doctype}/train/"
    body = {
        "source": training_data_blob_sas_url,
        "sourceFilter": {
            "prefix": prefix,
            "includeSubFolders": False
        },
        "useLabelFile": use_label_file
    }

    logging.info(f"Training url: {training_data_blob_sas_url}")

    try:
        resp = post(url=url, json=body, headers=headers)

        if resp.status_code == 201:
            status_url = resp.headers['Location']
            logging.info(f"Model analyse submitted. Operation Location: {status_url}")
            headers = {"Ocp-Apim-Subscription-Key": subscription_key}
            resp = get(url=status_url, headers=headers)
            logging.info(resp.json())
            count = 0
            max_retry = 500
            while (count < max_retry and resp.status_code == 200 and (resp.json()['modelInfo']['status'] == 'running' or resp.json()['modelInfo']['status'] == 'creating')):
                resp = get(url=status_url, headers=headers)
                time.sleep(0.5)
                count += 1
            logging.info(resp.json())
            return resp.json()
        else:
            logging.error(f"Error training: {str(resp.text)}")
    except Exception as e:
        logging.error(f"Error training model : {e}")
    
    return None


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
            logging.info(f"Invoice analyze submitted. Operation Location: {status_url}")
            headers = {"Ocp-Apim-Subscription-Key": subscription_key}
            resp = get(url=status_url, headers=headers)
            logging.info(resp.json())
            count = 0
            max_retry = 100
            while (count < max_retry and (resp.status_code == 200 or resp.status_code == 429) and (resp.json()['status'] == 'running' or resp.json()['status'] == 'notStarted')):
                resp = get(url=status_url, headers=headers)
                time.sleep(1)
                count += 1
            logging.info(resp.json()['status'])
            #print(resp.json())
            result = resp.json()['analyzeResult']
        else:
            logging.error(f"Error during analysis: {str(resp.text)}")
    except Exception as e:
        logging.error(f"Error analyzing invoice : {e}")

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
            logging.error(f"Prediction is invalid: {e}")
                
    return prediction


def batch_predictions(blobs, model_id, storage_url, container, sas, region, subscription_key):
    
    predictions = []

    try:
        count_analyzed = 0
        count_total = 0
        for blob in blobs:
            blob_url = storage_url + '/' + container + '/' + blob + sas
            logging.info(f"#{count_total} - Analyzing blob {blob}...")
            analyze_result = get_prediction(region, subscription_key, blob_url, model_id, "supervised")
            if len(analyze_result['fields']) > 0:
                logging.info("Done.")
                prediction = {}
                # Getting file ID from blob name
                prediction['file_id'] =  blob.split('/')[-1][:-4]
                prediction['fields'] = analyze_result['fields']
                predictions.append(prediction)
                count_analyzed += 1
            else:
                logging.error(f"Error analyzing blob {blob_url}: no fields were found.")
            count_total += 1
    except Exception as e:
        logging.error(f"Error during batch prediction: {e}")

    return predictions, count_analyzed, count_total


def analyze_layout(region, subscription_key, file_content, file_name):
    
    headers = {
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Content-Type": 'application/pdf'
    }

    operation_location = ""
    logging.info(f"Analyzing file {file_name}...")
    analyze_result_response = None

    try:
        url = f"https://{region}.api.cognitive.microsoft.com/formrecognizer/v2.0/layout/analyze"
        resp = post(url=url, data=file_content, headers=headers)
        logging.info(resp)
        operation_location = resp.headers['Operation-Location']
        logging.info(f"Analyze Operation Location: {operation_location}")
    except Exception as e:
        logging.error(f"Error analyzing file: {e}")

    # Getting response result
    if(operation_location != ""):
        resp_analyze = get(url=operation_location, headers=headers)
        analyze_result_response = resp_analyze.json()
        logging.info(analyze_result_response)
        count = 0
        max_retry = 30
        try:
            while(count < max_retry and resp_analyze.status_code == 200 and (analyze_result_response['status'] == 'running' or analyze_result_response['status'] == 'notStarted')):
                resp_analyze = get(url=operation_location, headers=headers)
                analyze_result_response = resp_analyze.json()
                time.sleep(0.5)
                count += 1
            logging.info(f"File {file_name} status: {analyze_result_response['status']}")
        except Exception as e:
            logging.error(f"Error analyzing file: {e}")
        
    return analyze_result_response


