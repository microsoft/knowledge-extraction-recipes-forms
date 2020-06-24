# This function is not intended to be invoked directly. Instead it will be
# triggered by an HTTP starter function.

import logging
import json

import azure.functions as func
import azure.durable_functions as df


def orchestrator_function(context: df.DurableOrchestrationContext):

    inputBlob = context.get_input()

    # Process image using OpenCV
    cleaned_form = yield context.call_activity("PreprocessForm", inputBlob["path"])

    # Classify model
    # TODO

    # Call Form Recognizer
    # form_recognizer_call = yield context.call_activity("CallFormRecognizer", "")

    # # TODO see if we can utilize call_http for 202 retry
    # # yield context.call_http()

    # # Retrieve Form Recognizer response
    # form_recognizer_response = yield context.call_activity(
    #     "RetrieveFormRecognizerResponse", ""
    # )

    # Post processing and entity extraction
    # postprocessed_result = yield context.call_activity("PostprocessForm", "")

    logging.warning([cleaned_form])

    return [cleaned_form]


main = df.Orchestrator.create(orchestrator_function)
