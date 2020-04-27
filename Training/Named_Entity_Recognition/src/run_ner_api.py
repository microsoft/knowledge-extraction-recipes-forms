"""
Created the Named Entity Recognition Evaluation API
"""

import json
import logging

from ast import literal_eval
from flask_restful.reqparse import RequestParser
from flask_restful_swagger_2 import swagger, Resource

from common.eval_ner import NerEvaluator

MODEL = 'model'
DOC = 'doc'
ENT_TYPES = 'ent_types'

class RunNerAPI(Resource):
    post_parser = RequestParser()

    # The following will define additional Swagger documentation for this API
    post_parser.add_argument(MODEL, type=str, required=False, location='args', help='The model_name provided as an arugment in the URI.')
    post_parser.add_argument(DOC, type=str, required=False, location='json', help='The document to extract named entitites from')
    post_parser.add_argument(ENT_TYPES, type=str, required=False, location='json', help='The accepted entities types passed in as a list')

    @swagger.doc({
        'tags': ['RunNerAPI'],
        'description': 'Run a trained Named Entity Recognition model on a document',
        'reqparser': {
            'name': 'RunNerAPI',
            'parser': post_parser
        },
        'responses': {
            '200': {
                'description': 'Return the recognised entities and their type',
                'examples': {
                    'application/json': "{\"Company LTD\": \"ORG\"}"
                }
            },
            '500': {
                'description': 'Unhandled error'
            }
        }
    })

    def post(self):
        args = self.post_parser.parse_args()
        model_name = ''
        doc = ''
        entity_types = ''

        try:
            model_name = args[MODEL]
        except Exception as e:
            logging.error(f'Failed to find the value in the URI: {str(e)}')
        
        try:
            data = args[DOC]
        except Exception as e:
            logging.error(f'Failed to find the value in the body: {str(e)}')      

        try:
            entity_types = args[ENT_TYPES]
            formatted_types = literal_eval(entity_types)
        except Exception as e:
            logging.error(f'Failed to find the value in the body: {str(e)}')
    
        evaluator = NerEvaluator()

        try:
            response = evaluator.run_ner_baseline(model_name, data, formatted_types)

            # If you need to JSONify the response, uncomment the following line
            response = json.dumps(response)

            return response, 200
        except Exception as e:
            logging.error(f'Failed to process the request: {str(e)}')

        return '', 500
