# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

# This function is not intended to be invoked directly. Instead it will be
# triggered by an Blob Trigger function.

# https://docs.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-code-constraints

import logging
import json

import azure.functions as func
import azure.durable_functions as df


def orchestrator_function(context: df.DurableOrchestrationContext):

    inputBlob = context.get_input()
    blob_path = inputBlob.get("path")
    logging.info("Orchestrator input: %s", inputBlob)

    # Classify model via Custom Vision / Text Classification / Model Compose?
    # TODO not implemented yet

    # Process incoming form using OpenCV
    blob_path_after_processing = yield context.call_activity(
        "PreProcessForm", blob_path
    )
    logging.info(
        "PreProcessForm activity finished with %s ", blob_path_after_processing
    )

    # Generate SAS token
    sas_token_url = yield context.call_activity(
        "GenerateSasToken", blob_path_after_processing
    )
    logging.info("GenerateSasToken activity finished with %s", sas_token_url)

    # Call Form Recognizer with SAS token url
    result = yield context.call_activity("CallFormRecognizer", sas_token_url)
    logging.info("CallFormRecognizer activity finished with %s", result)

    # # Retrieve Form Recognizer response
    # form_recognizer_response = yield context.call_activity(
    #     "RetrieveFormRecognizerResponse", ""
    # )

    # TODO Call Form Recognizer via Durable Functions Framework
    # response = yield context.call_http(
    #     "POST",
    #     uri,
    #     {"source": image},
    #     {"Ocp-Apim-Subscription-Key": key}
    # )

    # Post Processing and Entity Extraction
    result_after_post_processing = yield context.call_activity(
        "PostProcessText", result
    )

    # Write result to Blob Storage
    result_blob_path = yield context.call_activity(
        "SaveResultToBlobStorage",
        {"result": result_after_post_processing, "path": blob_path},
    )

    logging.info("SaveResultToBlobStorage activity finished with %s", result_blob_path)

    return result_blob_path


main = df.Orchestrator.create(orchestrator_function)
