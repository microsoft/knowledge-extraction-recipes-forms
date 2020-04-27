# This code is primary standard Form Recognizer code in Python. The only difference, we store successful model
# details in model.json file to use it in the next step

import argparse
import os
import json
import time
from requests import get, post
from azureml.core import Run
import logging

run = Run.get_context()

logging.basicConfig(level=logging.INFO)

log: logging.Logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser("train")
parser.add_argument("--sas_uri", type=str, required=True)
parser.add_argument("--output", type=str, required=True)
parser.add_argument("--fr_endpoint", type=str, required=True)
parser.add_argument("--fr_key", type=str, required=True)
args = parser.parse_args()

os.makedirs(args.output, exist_ok=True)
    

endpoint = args.fr_endpoint
post_url = endpoint + r"/formrecognizer/v2.0-preview/custom/models"
source = args.sas_uri
prefix = "Train"
includeSubFolders = False
useLabelFile = False

headers = {
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': args.fr_key,
}

body = 	{
    "source": source,
    "sourceFilter": {
        "prefix": prefix,
        "includeSubFolders": includeSubFolders
    },
    "useLabelFile": useLabelFile
}

try:
    resp = post(url = post_url, json = body, headers = headers)
    if resp.status_code != 201:
        log.error("POST model failed (%s):\n%s" % (resp.status_code, json.dumps(resp.json())))
        run.fail(error_details=json.dumps(resp.json()), error_code=resp.status_code)
    log.info("POST model succeeded:\n%s" % resp.headers)
    get_url = resp.headers["location"]
except Exception as e:
    log.error("POST model failed:\n%s" % str(e))
    run.fail(error_details=str(e)) 
    
n_tries = 15
n_try = 0
wait_sec = 5
max_wait_sec = 60
is_completed = False
while n_try < n_tries:
    try:
        resp = get(url = get_url, headers = headers)
        resp_json = resp.json()
        if resp.status_code != 200:
            log.error("GET model failed (%s):\n%s" % (resp.status_code, json.dumps(resp_json)))
            run.fail(error_details=json.dumps(resp.json()), error_code=resp.status_code)
        model_status = resp_json["modelInfo"]["status"]
        if model_status == "ready":
            log.info("Training succeeded:\n%s" % json.dumps(resp_json))
            is_completed = True
            with open(os.path.join(args.output, 'model.json'), 'w') as outfile:
                json.dump(resp_json, outfile)
            break
        if model_status == "invalid":
            log.error("Training failed. Model is invalid:\n%s" % json.dumps(resp_json))
            run.fail(error_details=json.dumps(resp.json()))
        time.sleep(wait_sec)
        n_try += 1
        wait_sec = min(2*wait_sec, max_wait_sec)     
    except Exception as e:
        msg = "GET model failed:\n%s" % str(e)
        log.error(msg)
        run.fail(error_details=str(e))
        
if is_completed is False:     
    log.error("Train operation did not complete within the allocated time.")
    run.fail(error_details="Train operation did not complete within the allocated time.")