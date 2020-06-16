#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging
import click
import json
from services import PredictDoc

from dotenv import load_dotenv
load_dotenv()

@click.command()
@click.option('-d','--doctype', prompt='Document Type Label',
              help='The document type you would like use for prediction.')
@click.option('-s','--source', prompt='Blob Sas Url',
              help='The document you would like to run a prediction on. This needs to be a blob sas url.')
def main(doctype, source):
    """Document Prediction """
    logging.getLogger().setLevel(logging.INFO)
    logging.info(f'Started document prediction for document type:{doctype} document:{source}')

    try:   
        predict_doc = PredictDoc()
        response = predict_doc.run(doctype, source)
        return print(json.dumps(response))        
    except Warning as we:
        logging.warn(we)
    except EnvironmentError as ee:
        logging.error(ee)
    except Exception as e:
        logging.error(e)


if __name__ == "__main__":
  main()