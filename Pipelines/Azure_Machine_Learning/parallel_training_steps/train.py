import argparse
import os
import json
import time
from requests import get, post
import logging
from azureml.core import Run

logging.basicConfig(level=logging.INFO)

log: logging.Logger = logging.getLogger(__name__)

def init():
    global args
    global frkey
    global sasuri

    log.info("Reading parameters")
    parser = argparse.ArgumentParser()
    parser.add_argument('--fr_endpoint', required=True)
    args, _ = parser.parse_known_args()
    run = Run.get_context()
    frkey = run.get_secret(name="frkey")
    sasuri = run.get_secret(name="sasuri")


def run(mini_batch):
    log.info("Starting minibatch execution")
    results = []
    if (mini_batch.empty):
        return results
    
    endpoint = args.fr_endpoint
    post_url = endpoint + r"/formrecognizer/v2.0-preview/custom/models"
    source = sasuri

    includeSubFolders = False
    useLabelFile = False

    headers = {
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': frkey,
    }

    for prefix in mini_batch["Folder"]:
        log.info(f"Training for folder {prefix}")

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
                continue
            log.info("POST model succeeded:\n%s" % resp.headers)
            get_url = resp.headers["location"]
        except Exception as e:
            log.error("POST model failed:\n%s" % str(e))
            continue 
    
        n_tries = 15
        n_try = 0
        wait_sec = 5
        max_wait_sec = 60
        while n_try < n_tries:
            try:
                resp = get(url = get_url, headers = headers)
                resp_json = resp.json()
                if resp.status_code != 200:
                    log.error("GET model failed (%s):\n%s" % (resp.status_code, json.dumps(resp_json)))
                    break
                model_status = resp_json["modelInfo"]["status"]
                if model_status == "ready":
                    log.info("Training succeeded:\n%s" % json.dumps(resp_json))
                    results.append("%s,%s" % (prefix, resp_json['modelInfo']['modelId']))
                    break
                if model_status == "invalid":
                    log.error("Training failed. Model is invalid:\n%s" % json.dumps(resp_json))
                    break
                time.sleep(wait_sec)
                n_try += 1
                wait_sec = min(2*wait_sec, max_wait_sec)     
            except Exception as e:
                msg = "GET model failed:\n%s" % str(e)
                log.error(msg)
                break
        
    return results
