#!/usr/bin/env python

import logging
import os

from applicationinsights.logging import enable
from applicationinsights import TelemetryClient
from flask import Flask
from flask_cors import CORS
from flask_restful_swagger_2 import Api, swagger

from common.benchmark_ner_api import NerBenchmarkAPI
from common.run_ner_api import RunNerAPI

APPLICATION_NAME = 'NamedEntityRecognition' # Used by Application Insights
ENV_VAR_FLASK_PORT = 'FLASK_PORT'
ENV_VAR_FLASK_DEBUG_MODE = 'FLASK_DEBUG_MODE'
ENV_VAR_APPLICATION_INSIGHTS_INSTRUMENTATION_KEY = 'APP_INSIGHTS_KEY'

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
api = Api(app, api_version='0.1', api_spec_url='/api/swagger')
flask_port = 5000
application_insights_instrumentation_key = ''
application_insights_handler = None

# This code gets run in the beginning of the first request
# Use this function to initialize services etc. if necessary.
@app.before_first_request
def initialize():   
    logging.getLogger().setLevel(logging.DEBUG)

api.add_resource(NerBenchmarkAPI, '/api/ner_eval')
api.add_resource(RunNerAPI, '/api/run_baseline')

@app.route('/')
def index():
    return f"""<head><meta http-equiv="refresh" content="0; url=http://petstore.swagger.io/?url=http://localhost:{flask_port}/api/swagger.json" /></head>"""

if __name__ == '__main__':
    run_flask_in_debug_mode = True

    try:
        application_insights_instrumentation_key = os.environ[ENV_VAR_APPLICATION_INSIGHTS_INSTRUMENTATION_KEY]
    except:
        logging.warning(f'No environment variable "{ENV_VAR_APPLICATION_INSIGHTS_INSTRUMENTATION_KEY}" set')
    
    if application_insights_instrumentation_key:
        telemetry_client = TelemetryClient(application_insights_instrumentation_key)        
        telemetry_client.context.device.role_name = APPLICATION_NAME
        application_insights_handler = enable(application_insights_instrumentation_key)
        logging.basicConfig(handlers=[application_insights_handler], format='%(levelname)s: %(message)s')

    try:
        flask_port = int(os.environ[ENV_VAR_FLASK_PORT])
    except:
        logging.warning(f'No environment variable "{ENV_VAR_FLASK_PORT}" set; using default port {flask_port}')
       
    try:
        run_flask_in_debug_mode = int(os.environ[ENV_VAR_FLASK_DEBUG_MODE])
    except:
        logging.warning(f'No environment variable "{ENV_VAR_FLASK_DEBUG_MODE}" set; will not run Flask in debug mode')

    app.run(host='0.0.0.0', port=flask_port, debug=run_flask_in_debug_mode)
