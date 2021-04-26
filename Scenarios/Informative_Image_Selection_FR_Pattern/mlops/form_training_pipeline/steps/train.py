# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Train Step for Form Recognizer
"""

# pylint: disable=wrong-import-order
# pylint: disable=ungrouped-imports
import json
from os.path import join
from typing import Dict
import logging
import click
from azureml.core.run import Run
from ml.models.formrecognizer.train_form import TrainFormRecognizer
from mlops.common.model_helpers import write_model_info


# define logger
logging.basicConfig(level=logging.INFO)
log: logging.Logger = logging.getLogger(__name__)


@click.command()
@click.option('--root_dir', type=click.STRING, required=True, help='Root directory of datastore')
@click.option('--train_dir', type=click.STRING, required=True,
              help='Path on blob containing training images and asset files')
@click.option('--model_info_dir', type=click.STRING, required=True,
              help='Path to folder containing trained model information')
def main(root_dir: str,
         train_dir: str,
         model_info_dir: str) -> None:
    """
    Main function for receiving args, and passing them through to form recognizer training function

    Parameters
    ----------
    root_dir: str
        Root datastore being used
    train_dir: str
        Path on blob containing training images and asset files
    model_info_dir: str
        Path to folder containing trained model information
    """
    log.info("Form Recognizer Training Step")

    # get context of current run
    run = Run.get_context()
    model_info_dir = join(root_dir, model_info_dir)

    # set form recognizer credentials
    form_credentials = {"key": run.get_secret("formkey"),
                        "endpoint": run.get_secret("formendpoint")}

    log.info("Training Custom Form Recognizer Model...")
    train_results = train_model(
        form_credentials=form_credentials,
        root_dir=root_dir,
        source_directory=train_dir,
        sas_uri=run.get_secret("formtrainsasuri")
    )

    # get model info and save results to JSON
    model_info = train_results["modelInfo"]

    if model_info is not None:
        filename = "model.json"
        write_model_info(model_info_dir, filename, model_info)
        log.info("Model info saved to model.json")
    else:
        log.info("Model information empty. Skipping write model information.")

    # Log metrics
    if "trainResult" in train_results:

        if "errors" in train_results["trainResult"] and len(train_results["trainResult"]["errors"]) > 0:
            log.error("Error training the model")
            log.error(f"train_results: \n{json.dumps(train_results, indent=4)}")
            return

        log.info("Logging metrics")
        avg_accuracy = train_results["trainResult"]["averageModelAccuracy"]
        run.parent.log(name="avg_accuracy", value=avg_accuracy)
        metrics = train_results["trainResult"]["fields"]
        for element in metrics:
            target = element["fieldName"]
            accuracy = element["accuracy"]
            run.parent.log(name=f"{target}_accuracy", value=accuracy)
    else:
        log.error("Error, could not find any metrics to log")


def train_model(form_credentials: dict,
                root_dir: str,
                source_directory: str,
                sas_uri: str) -> Dict:

    """
    Evaluates Form Recognizer model by computing detection
    rates on "scene" and "take" objects from clapperboardsVision model

    Parameters
    ----------
    form_credentials : dict
        Form Recognizer credentials
    root_dir: str
        Root datastore being used
    source_directory : str
        Path on blob containing label asset files
    sas_uri: str
        SAS URI used to train form recognizer model

    Returns
    -------
    Dict
       JSON object containing information about model training history
    """

    # invoke train endpoint and obtain get url
    log.info("Initiating Training Step")
    train_class = TrainFormRecognizer(apim_key=form_credentials["key"],
                                      endpoint=form_credentials["endpoint"])

    # Train custom model
    train_results = train_class.run_training(
        source=sas_uri,
        prefix=source_directory
    )

    return train_results


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
