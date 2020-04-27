#!/usr/bin/env python3

import logging
import click
import json
from services import TrainModel

from dotenv import load_dotenv
load_dotenv()

@click.command()
@click.option('-d','--doctype', prompt='Document Type Label',
              help='The document type you would like to train a model for.')
@click.option('-s','--supervised', prompt='Supervised',
              help='Set to true if you want to train in a supervised way, false if not')
@click.option('-u','--unsupervised', prompt='Unsupervised',
              help='Set to true if you want to train in an unsupervised way, false if not')
def main(doctype, supervised, unsupervised):
    """Forms Recognizer Model Training"""
    logging.getLogger().setLevel(logging.INFO)
    logging.info('TrainModel function processed a request')
    
    try:
        train_model = TrainModel()
        status, results = train_model.run(doctype, supervised, unsupervised)
        if results:
            return print(json.dumps(results))
        else:
            return print("Training finished, but could not create results file.")
                    
    except Warning as we:
        logging.warn(we)
    except EnvironmentError as ee:
        logging.error(ee)
    except Exception as e:
        logging.error(e)




if __name__ == "__main__":
  main()