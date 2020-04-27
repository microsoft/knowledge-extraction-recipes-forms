import json
import time
import argparse
import os
from requests import get, post
from azureml.core import Run, Model
import logging

run = Run.get_context()

logging.basicConfig(level=logging.INFO)

log: logging.Logger = logging.getLogger(__name__)

log.info("Reading parameters")
parser = argparse.ArgumentParser("score")
parser.add_argument("--output", type=str, required=True)
parser.add_argument("--fr_endpoint", type=str, required=True)
parser.add_argument("--fr_key", type=str, required=True)
args = parser.parse_args()

os.makedirs(args.output, exist_ok=True)

endpoint = args.fr_endpoint
apim_key = args.fr_key

log.info("Getting model id from metadata file")
ws = run.experiment.workspace
model_path = Model.get_model_path("basic_model", _workspace=ws)
with open(model_path, 'r') as fp:
    contents = fp.read()
    mapping = json.loads(contents)

model_id = mapping['modelInfo']['modelId']

log.info(f"Model Id is {model_id}")

headers = {
    'Content-Type': 'application/pdf',
    'Ocp-Apim-Subscription-Key': apim_key,
}

post_url = endpoint + "/formrecognizer/v2.0-preview/custom/models/%s/analyze" % model_id
params = {
    "includeTextDetails": True
}

log.info("List all files in the dataset folder")
with run.input_datasets["scoring_files"].mount() as mount_context:
    file_array = os.listdir(mount_context.mount_point)

    for file_item in file_array:
        log.info(f"Starting scoring process for {file_item}")
        with open(os.path.join(mount_context.mount_point, file_item), "rb") as f:
            data_bytes = f.read()

        try:
            resp = post(url = post_url, data = data_bytes, headers = headers, params = params)
            if resp.status_code != 202:
                log.error("POST analyze failed:\n%s" % json.dumps(resp.json()))
                run.fail(error_details=json.dumps(resp.json()), error_code=resp.status_code)
            log.info("POST analyze succeeded:\n%s" % resp.headers)
            get_url = resp.headers["operation-location"]
        except Exception as e:
            log.error("POST analyze failed:\n%s" % str(e))
            run.fail(error_details=str(e))  
    
        n_tries = 15
        n_try = 0
        wait_sec = 5
        max_wait_sec = 60
        is_completed = False
        while n_try < n_tries:
            try:
                resp = get(url = get_url, headers = {"Ocp-Apim-Subscription-Key": apim_key})
                resp_json = resp.json()
                if resp.status_code != 200:
                    log.error("GET analyze results failed:\n%s" % json.dumps(resp_json))
                    run.fail(error_details=json.dumps(resp.json()), error_code=resp.status_code)
                status = resp_json["status"]
                if status == "succeeded":
                    log.info("Analysis succeeded:\n%s" % json.dumps(resp_json))
                    is_completed = True
                    with open(os.path.join(args.output, file_item + '.json'), 'w') as outfile:
                        json.dump(resp_json, outfile)
                    break
                if status == "failed":
                    log.info("Analysis failed:\n%s" % json.dumps(resp_json))
                    run.fail(error_details=json.dumps(resp_json))
                time.sleep(wait_sec)
                n_try += 1
                wait_sec = min(2*wait_sec, max_wait_sec)     
            except Exception as e:
                msg = "GET analyze results failed:\n%s" % str(e)
                log.error(msg)
                run.fail(error_details=msg) 
                
        if is_completed is False:     
            log.error("Scoring operation did not complete within the allocated time.")
            run.fail(error_details="Scoring operation did not complete within the allocated time.")