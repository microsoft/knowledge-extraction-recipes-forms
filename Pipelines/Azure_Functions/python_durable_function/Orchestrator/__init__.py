# This function is not intended to be invoked directly. Instead it will be
# triggered by an Blob Trigger function.

import logging
import json

import azure.functions as func
import azure.durable_functions as df


def orchestrator_function(context: df.DurableOrchestrationContext):

    inputBlob = context.get_input()
    logging.warning("Orchestrator input: %s" , inputBlob)

    # Process image using OpenCV
    cleaned_form = yield context.call_activity("PreprocessFormWorkaround", inputBlob["path"])


    # Classify model
        # TODO
        # Custom Vision vs Text?

    # Call Form Recognizer
    # form_recognizer_call = yield context.call_activity("CallFormRecognizer", "")

    # # TODO see if we can utilize call_http for 202 retry

    # response = yield context.call_http(
    #     "POST",
    #     uri,
    #     {"source": image},
    #     {"Ocp-Apim-Subscription-Key": key}
    # )

    # print(type(response))
    # print(response)



    # # Retrieve Form Recognizer response
    # form_recognizer_response = yield context.call_activity(
    #     "RetrieveFormRecognizerResponse", ""
    # )

    # Post processing and entity extraction
    # postprocessed_result = yield context.call_activity("PostprocessForm", "")

    logging.warning([cleaned_form])

    return [cleaned_form]


main = df.Orchestrator.create(orchestrator_function)
