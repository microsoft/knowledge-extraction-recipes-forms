import logging
import os
from azureml.core import Run, Model
import argparse

logging.basicConfig(level=logging.INFO)

log: logging.Logger = logging.getLogger(__name__)
    
parser = argparse.ArgumentParser("register")
parser.add_argument("--input", type=str, required=True)
args = parser.parse_args()

run = Run.get_context()
ws = run.experiment.workspace

Model.register(model_path=os.path.join(args.input, "model.json"), model_name="multifolder_model", workspace=ws)