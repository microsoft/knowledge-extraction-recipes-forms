#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json
import logging
import os

from ast import literal_eval
from flask_restful.reqparse import RequestParser
from flask_restful_swagger_2 import swagger, Resource

import common.request_processor as request_processor

from dotenv import load_dotenv

load_dotenv()

STORAGE_NAME = os.environ['STORAGE_NAME']
STORAGE_KEY = os.environ['STORAGE_KEY']
VISION_KEY = os.environ['VISION_SUBSCRIPTION_KEY']
VISION_REGION = os.environ['VISION_REGION']
FORM_PATH = 'formPath'
OUTPUT_PATH = 'outputPath'


class CorrectSkewnessApi(Resource):
    post_parser = RequestParser()

    # The following will define additional Swagger documentation for this API
    post_parser.add_argument(FORM_PATH, type=str, required=True, location='json', help='The form path provided as part of the request body.')
    post_parser.add_argument(OUTPUT_PATH, type=str, required=False, location='json', help='The corrected form output path provided as part of the request body.')

    @swagger.doc({
        'tags': ['Skewness'],
        'description': 'Correct Skewness API.',
        'reqparser': {
            'name': 'CorrectSkewness',
            'parser': post_parser
        },
        'responses': {
            '200': {
                'description': 'Echo of the values given',
                'examples': {
                    'application/json': {
                        "formPath": "<value>",
                        "outputPath": "<value>"
                    }
                }
            },
            '500': {
                'description': 'Unhandled error'
            }
        }
    })
    def post(self):
        args = self.post_parser.parse_args()
        form_path = ''
        output_path = ''

        try:
            form_path = args[FORM_PATH]
        except Exception as e:
            logging.error(f'Failed to find the form path in the body: {str(e)}')        
        
        try:
            output_path = args[OUTPUT_PATH]
        except Exception as e:
            logging.error(f'Failed to find the output path in the body: {str(e)}')     
        
        response = request_processor.create_response_single(STORAGE_NAME, STORAGE_KEY, VISION_KEY, VISION_REGION, form_path, output_path)

        try:
            response_as_json = json.dumps(response)
            return response_as_json, 200
        except Exception as e:
            logging.error(f'Failed to JSONify the response: {str(e)}')

        return '', 500
