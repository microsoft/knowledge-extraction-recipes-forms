#!/usr/bin/env python3

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging
import click
import json
from services import ModelEvaluation

from dotenv import load_dotenv
load_dotenv()

@click.command()
@click.option('-d','--doctype', prompt='Document Type Label',
              help='The document type you would like to run evaluation on.')
@click.option('-r','--reuse', prompt='Reuse',
              help='True (reuse previously created evaluation file) or False (run predictions)')
def main(doctype, reuse):
    """Model Evaluation"""
    logging.getLogger().setLevel(logging.INFO)
    logging.info(f'Started model evaluation for {doctype}')

    try:
        model_evaluation = ModelEvaluation()
        print(reuse)
        response = model_evaluation.run(doctype, reuse)
        logging.info(response)
                    
    except Warning as we:
        logging.warn(we)
    except EnvironmentError as ee:
        logging.error(ee)
    except Exception as e:
        logging.error(e)


if __name__ == "__main__":
  main()