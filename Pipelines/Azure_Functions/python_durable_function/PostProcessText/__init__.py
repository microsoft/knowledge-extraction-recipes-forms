# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

# This function is not intended to be invoked directly. Instead it will be
# triggered by an orchestrator function.

import logging
import json

from azure.ai.formrecognizer import RecognizedForm


def main(result) -> str:

    result = json.loads(result)

    # Normalize text etc.

    for recognized_form in result:
        print("Form type ID: {}".format(recognized_form.get("form_type")))
        for label, field in recognized_form.get("fields").items():
            print(
                "Field '{}' has value '{}' with a confidence score of {}".format(
                    label, field.get("value"), field.get("confidence")
                )
            )

    # TODO Utilize typed RecognizedForm object
    # for recognized_form in result:
    #     recognized_form = RecognizedForm(
    #         page_range=recognized_form.get("page_range"),
    #         fields=recognized_form.get("fields"),
    #         form_type=recognized_form.get("form_type"),
    #         pages=recognized_form.get("pages"),
    #     )

    #     print("Form type ID: {}".format(recognized_form.form_type))
    #     for label, field in recognized_form.fields.items():
    #         print(
    #             "Field '{}' has value '{}' with a confidence score of {}".format(
    #                 label, field.value, field.confidence
    #             )
    #         )

    # Remove double spaces

    # Loop through

    # Field specific tweaks

    # Utilize custom dictionary
    processed_result = result

    return processed_result
