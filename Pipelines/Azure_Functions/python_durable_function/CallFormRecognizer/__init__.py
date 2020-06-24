# This function is not intended to be invoked directly. Instead it will be
# triggered by an orchestrator function.

import logging

from azure.ai.formrecognizer import FormRecognizerClient
from azure.core.credentials import AzureKeyCredential



def main(name: str) -> str:

    # TODO Move to env setttings + share client over requests?
    endpoint = "https://<region>.api.cognitive.microsoft.com/"
    credential = AzureKeyCredential("<api_key>")
    form_recognizer_client = FormRecognizerClient(endpoint, credential)
    model_id = "<your custom model id>"

    # TODO Receive Form URL with limited sas token

    poller = form_recognizer_client.begin_recognize_custom_forms_from_url(model_id=model_id, form_url="form_url")

    # TODO abstract poller
    result = poller.result()

    for recognized_form in result:
        print("Form type ID: {}".format(recognized_form.form_type))
        for label, field in recognized_form.fields.items():
            print("Field '{}' has value '{}' with a confidence score of {}".format(
                label, field.value, field.confidence
            ))
    
    return f"Hello {name}!"
