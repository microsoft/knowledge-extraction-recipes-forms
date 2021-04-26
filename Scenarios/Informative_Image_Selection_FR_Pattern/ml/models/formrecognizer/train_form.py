# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Script containing set of functions used to train a custom form recognizer service
"""

import json
import time
from requests import get, post
from requests.exceptions import RequestException


class TrainFormRecognizer:
    """
    Wrapper for the Form Recognizer Train API
    """

    def __init__(self, apim_key: str, endpoint: str):
        """Constructs an instance of the TrainFormRecognizer class

        Parameters
        ----------
        endpoint: String
            Endpoint to form recognizer resource
        apim_key: String
            API key for form recognizer resource
        """
        self.apim_key = apim_key
        self.endpoint = endpoint

    def train_custom_model(self,
                           source: str,
                           prefix: str) -> dict:

        """
        Function used to train a custom form recognizer model

        Parameters
        ----------
        source: String
            SAS URL for blob container where labeled
            files and OCR results are located
        prefix: String
            Path to folder or subdirectory containing
            labels and OCR results

        Raises
        ------
        RequestException
            If the response status is not 200
        Exception
            If specified path on blob does not exist

        Returns
        -------
        Dict
            Object containing information regarding to
            trained custom model
        """

        n_tries = 3
        n_try = 0
        wait_sec = 5
        max_wait_sec = 60

        get_url = ""
        post_url = self.endpoint + r"/formrecognizer/v2.0/custom/models"
        include_sub_folders = False
        use_label_file = True

        headers = {
            # Request headers
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': self.apim_key,
        }

        body = {
            "source": source,
            "sourceFilter": {
                "prefix": prefix,
                "includeSubFolders": include_sub_folders
            },
            "useLabelFile": use_label_file
        }

        while n_try < n_tries:
            try:
                resp = post(url=post_url, json=body, headers=headers)
                if resp.status_code != 201:
                    print("POST model failed (%s):\n%s" % (resp.status_code, json.dumps(resp.json())))
                    get_url = resp.json()
                if resp.status_code == 201:
                    print("POST model succeeded:\n%s" % resp.headers)
                    get_url = resp.headers["location"]
                    return get_url

                # we didn't retrieve a get url. try again
                time.sleep(wait_sec)
                n_try += 1
                wait_sec = min(2 * wait_sec, max_wait_sec)

            except RequestException as err_msg:
                print("POST model failed:\n%s" % str(err_msg))

    def get_train_results(self,
                          get_url: str) -> dict:

        """
        Function used to get status and results of current
        training operation regarding custom form recognizer service

        Parameters
        ----------
        get_url: String
            Endpoint used to query status of train operation
            for a particular form recognizer service.
            Endpoint should be returned when training operation
            is invoked.

        Raises
        ------
        RequestException
            If the response status is not 200
        Exception
            If invalid GET URL is passed into request

        Returns
        -------
        Dict
            Object containing information regarding to
            trained custom model
        """

        headers = {
            # Request headers
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': self.apim_key,
        }

        n_tries = 15
        n_try = 0
        wait_sec = 5
        max_wait_sec = 60
        while n_try < n_tries:
            try:
                resp = get(url=get_url, headers=headers)
                resp_json = resp.json()
                if resp.status_code != 200:
                    print("GET model failed (%s):\n%s" % (resp.status_code, json.dumps(resp_json)))
                    return resp_json

                model_status = resp_json["modelInfo"]["status"]
                if model_status == "ready":
                    print("Training succeeded:\n%s" % json.dumps(resp_json))
                    return resp_json

                if model_status == "invalid":
                    print("Training failed. Model is invalid:\n%s" % json.dumps(resp_json))
                    return resp_json

                # Training still running. Wait and retry.
                time.sleep(wait_sec)
                n_try += 1
                wait_sec = min(2 * wait_sec, max_wait_sec)

            except RequestException as err_msg:
                raise Exception from err_msg
        print("Train operation did not complete within the allocated time.")

    def run_training(self,
                     source: str,
                     prefix: str) -> dict:

        """
        Function that trains a custom form recognizer model and returns
        training progress and results

        Parameters
        ----------
        source: String
            SAS URL for blob container where labeled
            files and OCR results are located
        prefix: String
            Path to folder or subdirectory containing
            labels and OCR results

        Raises
        ------
        RequestException
            If the response status is not 200
        Exception
            If invalid GET URL is passed into request

        Returns
        -------
        Dict
            Object containing information regarding to
            trained custom model
        """
        # invoke functions to feed image and query results from model
        try:
            # invoke train function and retrieve get url
            get_url = self.train_custom_model(source=source, prefix=prefix)
            # query train results and retrieve model ID and results
            train_results = self.get_train_results(get_url=get_url)
            return train_results
        except (RequestException) as err_msg:
            raise Exception from err_msg
