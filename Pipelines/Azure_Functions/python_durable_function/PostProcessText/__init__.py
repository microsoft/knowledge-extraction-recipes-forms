# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

# This function is not intended to be invoked directly. Instead it will be
# triggered by an orchestrator function.

import logging
import json

from azure.ai.formrecognizer import RecognizedForm


def main(result) -> str:

    result = json.loads(result)

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

    # Normalize text etc.
    processed_result = []

    for recognized_form in result:
        logging.debug("Form type ID: {}".format(recognized_form.get("form_type")))

        for label, field in recognized_form.get("fields").items():
            logging.debug(
                "Field '{}' has value '{}' with a confidence score of {}".format(
                    label, field.get("value"), field.get("confidence")
                )
            )

            value = field.get("value")

            # Take an action based on the confidence level of the OCR data
            value_data = field.get("value_data")
            ocr_confidence = []

            if value_data is not None:
                text_content = value_data.get("text_content")

                for content in text_content:
                    if content is None:
                        continue

                    text = content.get("text")
                    confidence = content.get("confidence")
                    page_number = content.get("page_number")

                    ocr_confidence.append(
                        {
                            "text": text,
                            "confidence": confidence,
                            "page_number": page_number,
                        }
                    )

            # Add your text transformations here, for example the removal of extra spaces
            # and field specific tweaks using a custom dictionary
            if label == "TestLabel":
                value = value.strip()

            # Add label and value to final result
            processed_result.append(
                {
                    "name": field.get("name"),
                    "value": value,
                    "fr_confidence": field.get("confidence"),
                    "ocr_confidence": ocr_confidence,
                }
            )

    return processed_result
