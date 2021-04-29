# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Evaluation Step for Form Recognizer
"""

# pylint: disable=wrong-import-order
# pylint: disable=ungrouped-imports
import os
import json
from os.path import join
from typing import Dict, List
import logging
from azureml.core.run import Run

import click
import pandas as pd
from ml.models.formrecognizer.utils import (compute_detection_rate, get_results)


# define logger
logging.basicConfig(level=logging.INFO)
log: logging.Logger = logging.getLogger(__name__)


# pylint: disable=too-many-locals
@click.command()
@click.option('--root_dir', type=click.STRING, required=True, help='Root directory of datastore')
@click.option('--model_info_dir', type=click.STRING, required=True, help='Directory containing model information')
@click.option('--val_dir', type=click.STRING, required=True, help='Path to the folder containing test images')
@click.option('--output_dir', type=click.STRING, required=True, help='Path to the folder to save the result in')
@click.option('--labels', type=click.STRING, required=True,
              help="Labels the custom model was trained on as well as fields to extract results from")
def main(root_dir: str,
         model_info_dir: str,
         val_dir: str,
         output_dir: str,
         labels: str) -> None:
    """
    Main function for receiving args, and passing them through to form recognizer postprocessing function

    Parameters
    ----------
    root_dir: str
        Root datastore being used
    model_info_dir: str
        Directory containing trained custom model information
    val_dir: str
        Directory containing test images
    output_dir: str
        Path to save outputs to
    labels: str
        Labels or fields to extract results from
    """
    log.info("Evaluation step")

    # get context of current run
    run = Run.get_context()

    # set form recognizer credentials
    form_credentials = {"key": run.get_secret("formkey"),
                        "endpoint": run.get_secret("formendpoint")}

    # process labels string to array
    labels = [label.strip() for label in labels.split(",")]

    model_info_dir = join(root_dir, model_info_dir)
    val_dir = join(root_dir, val_dir)
    output_dir = join(root_dir, output_dir)

    # read in model information
    log.info("Compile model information")
    model_fname = "model.json"
    with open(join(model_info_dir, model_fname), "r") as model_info_file:
        model_info = json.load(model_info_file)
        log.info(model_info)

    # Processing image files
    images = []
    for file in os.listdir(val_dir):
        images.append({"image": file})

    # convert array of dict objects to a pandas dataframe
    image_df = pd.DataFrame(images)
    # use lambda function to aply full path to each image file
    image_df["image"] = image_df["image"].apply(
        lambda x: join(val_dir, x)
    )

    log.info("Evaluate Form Recognizer Model")
    detection_rates = get_detection_rates(
        form_credentials=form_credentials,
        model_id=model_info["modelId"],
        image_df=image_df,
        output_dir=output_dir,
        labels=labels
    )

    # Log metrics
    for metric_info in detection_rates:
        # extract and log detection rate for each object per video
        scene_rate = metric_info["scene_detection_rate"]
        take_rate = metric_info["take_detection_rate"]
        run.parent.log(name="scene_detection_rate", value=scene_rate)
        run.parent.log(name="take_detection_rate", value=take_rate)

    log.info("Finished model evaluation")


def get_detection_rates(form_credentials: dict,
                        model_id: str,
                        image_df: pd.DataFrame,
                        output_dir: str,
                        labels: List) -> List[Dict]:
    """
    Evaluates Form Recognizer model by computing detection
    rates on "scene" and "take" objects from clapperboardsVision model

    Parameters
    ----------
    form_credentials : FormRecognizerPipelineSecrets
        Form Recognizer credentials
    model_id: str
        ID of the custom model being used
    image_df  pd.DataFrame
        Dataframe containing test images
    output_dir : str
        Directory to save Form Recognizer evaluation results in
    labels: Array
        Labels or fields to extract results from

    Returns
    -------
    List[Dict]
        Detection rates for "scene" and "take" for each video
    """
    # check if output from previous run exists, if not, generate new results
    os.makedirs(output_dir, exist_ok=True)
    if len(os.listdir(output_dir)) == 0:
        log.info("Run Custom Form Recognizer Prediction")
        # make test directory to store results
        output_file = join(output_dir, "form_results.csv")
        # feed parameters into get_results function
        get_results(
            image_df=image_df,
            output_file=output_file,
            endpoint=form_credentials["endpoint"],
            apim_key=form_credentials["key"],
            model_id=model_id,
            labels=labels
        )
    else:
        log.info("Found existing Form Recognizer Predictions. Skipping prediction...")

    log.info("Compute Detection Rates")
    # Pass in directory with predictions
    detection_rates = compute_detection_rate(input_dir=output_dir, output_dir=join(output_dir, "evaluation"))

    return detection_rates


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
