#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json
import logging
import os

from flask_restful.reqparse import RequestParser
from flask_restful_swagger_2 import swagger, Resource

import common.request_processor as request_processor

from dotenv import load_dotenv
load_dotenv()


STORAGE_NAME = os.environ['STORAGE_NAME']
STORAGE_KEY = os.environ['STORAGE_KEY']
VISION_KEY = os.environ['VISION_SUBSCRIPTION_KEY']
VISION_REGION = os.environ['VISION_REGION']
CONTAINER = 'container'
OUTPUT_CONTAINER = 'outputContainer'


class CorrectSkewnessBatchApi(Resource):
    post_parser = RequestParser()

    # The following will define additional Swagger documentation for this API
    post_parser.add_argument(CONTAINER, type=str, required=True, location='json', help='The container name provided as part of the request body.')
    post_parser.add_argument(OUTPUT_CONTAINER, type=str, required=True, location='json', help='The output container provided as part of the request body.')

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
                        "container": "<value found in body>",
                        "outputContainer": "<value found in body>"
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
        container = ''
        output_container = ''

        try:
            container = args[CONTAINER]
        except Exception as e:
            logging.error(f'Failed to find the container name in the body: {str(e)}')        
        
        try:
            output_container = args[OUTPUT_CONTAINER]
        except Exception as e:
            logging.error(f'Failed to find the output container name in the body: {str(e)}')     
        
        response = request_processor.create_response_batch(STORAGE_NAME, STORAGE_KEY, VISION_KEY, VISION_REGION, container, output_container)

        try:
            response_as_json = json.dumps(response)
            return response_as_json, 200
        except Exception as e:
            logging.error(f'Failed to JSONify the response: {str(e)}')

        return '', 500

