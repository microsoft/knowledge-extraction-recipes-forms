#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Created the Named Entity Recognition Evaluation API
"""
import logging

from ast import literal_eval
from flask_restful.reqparse import RequestParser
from flask_restful_swagger_2 import swagger, Resource

from common.eval_ner import NerEvaluator

MODEL = 'model'
EVAL_TESTSET = 'eval_dataset'
ENT_TYPES = 'ent_types'


class NerBenchmarkAPI(Resource):
    post_parser = RequestParser()

    # The following will define additional Swagger documentation for this API
    post_parser.add_argument(MODEL, type=str, required=False, location='args', help='The model_name provided as an arugment in the URI.')
    post_parser.add_argument(EVAL_TESTSET, 
                            type=str, required=False, location='json', 
                            help='The evaluation dataset in the following format [["<doc_text>",{"entities:[[<start_pos>,<end_pos>,"<ENTITY_TYPE>"], [<start_pos>,<end_pos>,"<ENTITY_TYPE>"]]}]] ')
    post_parser.add_argument(ENT_TYPES, type=str, required=False, location='json', help='The accepted entities types passed in as a list')

    @swagger.doc({
        'tags': ['NerBenchmarkAPI'],
        'description': 'Benchmark Named Entity Recognition model',
        'reqparser': {
            'name': 'NerBenchmarkAPI',
            'parser': post_parser
        },
        'responses': {
            '200': {
                'description': 'Benchmark a trained named entity model on an evaluation set',
                'examples': {
                        'application/json': {
                            "uas": 0,
                            "las": 0,
                            "ents_p": 80,
                            "ents_r": 100,
                            "ents_f": 88.8888888888889,
                            "ents_per_type": {
                                "ORG": {
                                    "p": 100,
                                    "r": 100,
                                    "f": 100
                                },
                                "MONEY": {
                                    "p": 0,
                                    "r": 0,
                                    "f": 0
                                },
                                "GPE": {
                                    "p": 100,
                                    "r": 100,
                                    "f": 100
                                }
                            },
                            "tags_acc": 0,
                            "token_acc": 100,
                            "textcat_score": 0,
                            "textcats_per_cat": {}
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
        model_name = ''
        eval_set = ''
        entity_types = ''

        try:
            model_name = args[MODEL]
        except Exception as e:
            logging.error(f'Failed to find the value in the URI: {str(e)}')
        
        try:
            eval_set = args[EVAL_TESTSET]
            formatted_set = literal_eval(eval_set)
        except Exception as e:
            logging.error(f'Failed to find the value in the body: {str(e)}')      

        try:
            entity_types = args[ENT_TYPES]
            formatted_types = literal_eval(entity_types)
        except Exception as e:
            logging.error(f'Failed to find the value in the body: {str(e)}')      
        evaluator = NerEvaluator()

        try:
            response = evaluator.evaluate_ner_baseline(model_name, formatted_set, formatted_types)

            # If you need to JSONify the response, uncomment the following line
            #response = json.dumps(response)

            return response, 200
        except Exception as e:
            logging.error(f'Failed to process the request: {str(e)}')

        return '', 500
