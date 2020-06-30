# This function is not intended to be invoked directly. Instead it will be
# triggered by an orchestrator function.

import logging
import os 
import datetime

from azure.ai.formrecognizer import FormRecognizerClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, ResourceTypes, AccountSasPermissions


def main(name: str) -> str:

    # Get blob name and container from path
    container = path.split('/')[0]
    blob = "/".join(path.split('/')[1:])

    # TODO Handle retry logic? 
    # # TODO Move to env setttings + share client over requests?
    # endpoint = "https://<region>.api.cognitive.microsoft.com/"
    # credential = AzureKeyCredential("<api_key>")
    # form_recognizer_client = FormRecognizerClient(endpoint, credential)
    # model_id = "<your custom model id>"

    # Create a temporary SAS token for Form Recognizer
    blob_service_client = BlobServiceClient.from_connection_string(os.environ["pythonfrpipeline_STORAGE"])
    blob_container_client = blob_service_client.get_container_client(container)

    sas_token = generate_blob_sas(
        account_name=blob_container_client.account_name,
        account_key=blob_container_client.credential.account_key,
        container_name=blob_container_client.container_name,
        blob_name=blob,
        permission=AccountSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(minutes=15),
    )
    url = blob_client.url + "?" + sas_token

    # poller = form_recognizer_client.begin_recognize_custom_forms_from_url(
    #     model_id=model_id, form_url="form_url"
    # )

    # # TODO abstract poller
    # result = poller.result()

    # for recognized_form in result:
    #     print("Form type ID: {}".format(recognized_form.form_type))
    #     for label, field in recognized_form.fields.items():
    #         print(
    #             "Field '{}' has value '{}' with a confidence score of {}".format(
    #                 label, field.value, field.confidence
    #             )
    #         )

    return f"Hello {name}!"
