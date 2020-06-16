#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging
import os

from flask import Flask
from flask_cors import CORS
from flask_restful_swagger_2 import Api, swagger

from common.correctSkewness import CorrectSkewnessApi
from common.correctSkewnessBatch import CorrectSkewnessBatchApi

ENV_VAR_FLASK_DEBUG_MODE = 'FLASK_DEBUG_MODE'

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
api = Api(app, api_version='0.1', api_spec_url='/api/swagger')

# This code gets run in the beginning of the first request
# Use this function to initialize services etc. if necessary.
@app.before_first_request
def initialize():
    logging.getLogger().setLevel(logging.DEBUG)

api.add_resource(CorrectSkewnessApi, '/api/correctSkewness')
api.add_resource(CorrectSkewnessBatchApi, '/api/correctSkewnessBatch')

@app.route('/')
def index():
    return """<head><meta http-equiv="refresh" content="0; url=http://petstore.swagger.io/?url=http://localhost:5000/api/swagger.json" /></head>"""

if __name__ == '__main__':
    run_flask_in_debug_mode = False

    try:
        run_flask_in_debug_mode = int(os.environ[ENV_VAR_FLASK_DEBUG_MODE])
    except:
        logging.warning(f'No environment variable "{ENV_VAR_FLASK_DEBUG_MODE}" set; will not run Flask in debug mode')

    app.run(host='0.0.0.0', debug=run_flask_in_debug_mode)
