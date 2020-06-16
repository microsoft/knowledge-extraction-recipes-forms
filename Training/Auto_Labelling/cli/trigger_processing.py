#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import click
from services import TriggerProcessor, QueueProcessor

from dotenv import load_dotenv
load_dotenv()

@click.command()
@click.option('-d','--doctype', prompt='Document Type label',
              help='The document type you would like to trigger processing for.')
@click.option('-s','--status', prompt='Status',
              help='Set status to new, ocr-done, keep or done')

def main(doctype, status):
    try:
      trigger_processor = TriggerProcessor()
      queue_processor = QueueProcessor()
      trigger_processor.run(doctype, status, queue_processor, True)
      print(f"Processing for doctype {doctype} started.")
    except NameError as ne:
      print(ne)
    except EnvironmentError as ee:
      print(ee)          
    except Exception as e:
      print(e)

if __name__ == "__main__":
  main()
