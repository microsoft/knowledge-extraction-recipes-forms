# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

# This function is not intended to be invoked directly. Instead it will be
# triggered by an orchestrator function.

import logging
import os
import datetime
import json

from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import RecognizedForm
from azure.ai.formrecognizer.aio import FormRecognizerClient

from typing import List


async def main(sasTokenUrl: str) -> List[RecognizedForm]:

    form_url = sasTokenUrl

    endpoint = os.environ["FormRecognizer_Endpoint"]
    credential = AzureKeyCredential(os.environ["FormRecognizer_SubscriptionKey"])
    model_id = os.environ["FormRecognizer_ModelId"]

    async with FormRecognizerClient(
        endpoint=endpoint, credential=credential
    ) as form_recognizer_client:

        poller = await form_recognizer_client.begin_recognize_custom_forms_from_url(
            model_id=model_id, form_url=form_url, include_text_content=True
        )

        # TODO Remove poller, move to seperate Activity Function to limit execution time and save costs
        result = await poller.result()
        recognized_form_json = json.dumps(result, default=lambda x: x.__dict__)

        return recognized_form_json
