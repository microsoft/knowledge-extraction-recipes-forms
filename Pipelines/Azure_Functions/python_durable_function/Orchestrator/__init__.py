# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

# This function is not intended to be invoked directly. Instead it will be
# triggered by an Blob Trigger function.

import logging
import json

import azure.functions as func
import azure.durable_functions as df


def orchestrator_function(context: df.DurableOrchestrationContext):

    inputBlob = context.get_input()
    logging.warning("Orchestrator input: %s", inputBlob)

    originalPath = inputBlob.get("path")

    # Process image using OpenCV
    originalPath, processedPath = yield context.call_activity(
        "PreProcessForm", inputBlob["path"]
    )
    logging.warning("PreProcessForm done %s %s", originalPath, processedPath)

    # Classify model
    # TODO
    # Custom Vision / Text Classification / Model Compose?

    # Generate SAS token
    sas_token_url = yield context.call_activity("GenerateSasToken", processedPath)
    logging.warning("GenerateSasToken done %s", sas_token_url)

    # Call Form Recognizer with SAS token url
    result = yield context.call_activity("CallFormRecognizer", sas_token_url)
    logging.warning("CallFormRecognizer done %s", result)

    # # Retrieve Form Recognizer response
    # form_recognizer_response = yield context.call_activity(
    #     "RetrieveFormRecognizerResponse", ""
    # )

    # Call Form Recognizer via Durable Functions Framework
    # response = yield context.call_http(
    #     "POST",
    #     uri,
    #     {"source": image},
    #     {"Ocp-Apim-Subscription-Key": key}
    # )

    # Post processing and entity extraction
    postprocessed_result = yield context.call_activity("PostProcessText", result)

    # Write result to Blob Storage
    resultPath = yield context.call_activity(
        "SaveResultToBlobStorage",
        {"result": postprocessed_result, "path": originalPath},
    )

    logging.warning("DONE")

    return resultPath


main = df.Orchestrator.create(orchestrator_function)
