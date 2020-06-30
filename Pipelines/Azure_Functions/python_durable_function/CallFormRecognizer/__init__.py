# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

# This function is not intended to be invoked directly. Instead it will be
# triggered by an orchestrator function.

import logging
import os
import datetime
import json

from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import FormRecognizerClient, RecognizedForm

def main(sasTokenUrl: str) -> RecognizedForm:

    form_url = sasTokenUrl

    endpoint = os.environ["FormRecognizer_Endpoint"]
    credential = AzureKeyCredential(os.environ["FormRecognizer_SubscriptionKey"])
    form_recognizer_client = FormRecognizerClient(endpoint, credential)
    model_id = os.environ["FormRecognizer_ModelId"]

    poller = form_recognizer_client.begin_recognize_custom_forms_from_url(
        model_id=model_id, form_url=form_url
    )

    # TODO Remove poller, move to seperate Activity Function 
    result = poller.result()

    # TODO Make RecognizedForm JSON serializable 

    temp_result = []

    # Normalize text etc.
    for recognized_form in result:
        print("Form type ID: {}".format(recognized_form.form_type))
        for label, field in recognized_form.fields.items():

            temp_result.append({
                "label": label, 
                "value": field.value,
                "confidence": field.confidence
            })

            print(
                "Field '{}' has value '{}' with a confidence score of {}".format(
                    label, field.value, field.confidence
                )
            )
        
        return temp_result



