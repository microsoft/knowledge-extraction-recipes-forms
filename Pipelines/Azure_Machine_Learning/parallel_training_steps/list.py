import argparse
import os
import csv
from azureml.core import Run
import logging

run = Run.get_context()

logging.basicConfig(level=logging.INFO)

log: logging.Logger = logging.getLogger(__name__)

log.info("Reading parameters")    

parser = argparse.ArgumentParser("list")
parser.add_argument("--list_output", type=str, required=True)
parser.add_argument("--training_folder", type=str, required=True)
args = parser.parse_args()

os.makedirs(args.list_output, exist_ok=True)

log.info("Reading folders to a list")
subfolders = os.listdir(args.training_folder)

output_file = os.path.join(args.list_output, "folders.csv")
log.info(f"Output file is {output_file}")

with open(output_file, 'w') as result:
    wr = csv.writer(result)
    wr.writerow(["Folder"])
    for folder in subfolders:
        log.info(f"Writing folder: {folder}")
        wr.writerow([folder])