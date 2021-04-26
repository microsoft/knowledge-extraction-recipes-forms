# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Model registration Step for Custom Form Recognizer Pipeline
"""

import os
from os.path import join
import logging
import json
import click
from azureml.core import Run

from mlops.common.model_helpers import write_model_info

# define logger
logging.basicConfig(level=logging.INFO)
log: logging.Logger = logging.getLogger(__name__)


@click.command()
@click.option('--root_dir', type=click.STRING, required=True, help='Root directory of datastore')
@click.option("--build_id", type=click.STRING, help="pipeline build ID", required=False)
@click.option("--model_name", type=click.STRING, help="Name of the model to use for registration", required=True)
@click.option("--model_info_dir", type=click.STRING,
              help="Path to folder containing trained model information", required=True)
@click.option("--dataset_path", type=click.STRING, help="Path to dataset used for training", required=True)
@click.option("--git_hash", type=click.STRING, help="Hash of the current git commit", required=False)
def main(root_dir: str,
         build_id: str,
         model_name: str,
         model_info_dir: str,
         dataset_path: str,
         git_hash: str):
    """
    Main function for receiving args, and passing them through to register a Custom Form Recognizer model

    Parameters
    ----------
    root_dir: str
        Root datastore being used
    build_id: str
        Pipeline build ID
    model_name: str
        Name of the model used for registration
    model_info_dir: str
        Path to directory containing model information
    dataset_path: str
        Path to directory containing dataset used for training
    git_hash: str
        Hash of the current git commit
    """
    log.info("Registration step")

    dataset_path = join(root_dir, dataset_path)

    # Compile model information
    log.info("Compile model information")
    model_fname = "model.json"
    with open(join(model_info_dir, model_fname), "r") as model_info_file:
        model_info = json.load(model_info_file)

    # load dataset save info for registration step
    dataset_files = os.listdir(dataset_path)
    labels_info = {}
    labels_info["documentLabels"] = [file for file in dataset_files if file.endswith(".labels.json")]
    dataset_info = {}
    dataset_info["images"] = [file for file in dataset_files if file.endswith(".jpeg")]
    dataset_info["ocr"] = [file for file in dataset_files if file.endswith(".ocr.json")]

    hyperparams = {
        "git_hash": git_hash,
        "build_id": build_id
    }

    # save dataset and label info to model directory
    model_dir = "outputs"
    write_model_info(model_dir, "model.json", model_info)
    json.dump(labels_info, open(join(model_dir, "labels.json"), 'w'))
    json.dump(dataset_info, open(join(model_dir, "dataset.json"), 'w'))

    # Registering everything as a model
    log.info("Register model")
    run = Run.get_context()
    run.upload_folder(model_dir, model_dir)
    model = run.register_model(
        model_name=model_name, model_path=model_dir, tags=hyperparams
    )
    return model


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
