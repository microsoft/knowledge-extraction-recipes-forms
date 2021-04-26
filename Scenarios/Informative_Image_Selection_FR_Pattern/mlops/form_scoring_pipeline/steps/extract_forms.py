# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Step to feed images in custom form recognizer endpoint
"""

import os
from os.path import join
from pathlib import Path
import logging

import click
from tqdm.notebook import tqdm
import pandas as pd
from azureml.core.run import Run

from ml.models.formrecognizer.form_recognizer_utilities import (
    extract_text_items,
    extract_metadata,
    run_analysis,
)


# pylint: disable=too-many-locals
# pylint: disable=bad-docstring-quotes

# define logger
logging.basicConfig(level=logging.INFO)
log: logging.Logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--root_dir", type=click.STRING, required=True, help="Root directory of datastore"
)
@click.option(
    "--input_dir",
    type=click.STRING,
    required=True,
    help="Path to the folder containing input images",
)
@click.option(
    "--clapperboard_dir",
    type=click.STRING,
    required=True,
    help="Path to the folder containing selected clapperboards",
)
@click.option(
    "--output_dir",
    type=click.STRING,
    required=True,
    help="Path to the folder to save the result in",
)
@click.option(
    "--labels",
    type=click.STRING,
    required=True,
    help="Labels the custom model was trained on as well as fields to extract results from",
)
@click.option(
    "--force",
    default=False,
    type=bool,
    help="Overwrite the results in the specified output folder",
)
def main(root_dir: str,
         input_dir: str,
         clapperboard_dir,
         output_dir: str,
         labels: str,
         force: bool) -> None:
    """
    Main function for receiving args, and passing them through to form recognizer postprocessing function

    Parameters
    ----------
    root_dir: str
        Root datastore being used
    input_dir: str
        Directory containing input data
    clapperboard_dir: str
        Direcotry containing selected clapperboards
    output_dir: str
        Path to save outputs to
    labels: str
        Labels or fields to extract results from
    force: bool
        Flag that specifies whether current run
        should overwrite outputs from previous run
    """

    log.info("Form Recognizer Extraction step")

    # get current run context
    run = Run.get_context()

    # set form recognizer credentials
    form_credentials = {"key": run.get_secret("formkey"),
                        "endpoint": run.get_secret("formendpoint")}
    model_id = run.get_secret("formmodelid")

    # Resolve paths
    input_dir = join(root_dir, input_dir)
    output_dir = join(root_dir, output_dir, "form_results")
    clapperboard_dir = join(root_dir, clapperboard_dir)

    log.info("Checking if output from previous run exists...")
    if os.path.exists(output_dir) and not force:
        log.info("Output path already exists, please use --force to overwrite the results. Skipping...")
        return

    # Create directory to store results in
    os.makedirs(output_dir, exist_ok=True)

    # Processing image files
    log.info("Running Form Recognizer Prediction...")
    for file in os.listdir(clapperboard_dir):
        image_df = pd.read_csv(join(clapperboard_dir, file))
        image_df["image"] = image_df["image"].apply(
                lambda x: join(input_dir, x)
            )
        # set output file
        output_file = os.path.join(output_dir, "results.csv")
        # process labels string to array
        labels = [label.strip() for label in labels.split(",")]

        # invoke form recognizer extraction function
        run_custom_form_model(
            form_credentials=form_credentials,
            image_df=image_df,
            output_file=output_file,
            model_id=model_id,
            labels=labels
        )

    log.info("Finished Running Form Recognizer Step.")


def run_custom_form_model(image_df: pd.DataFrame,
                          output_file: str,
                          form_credentials: dict,
                          model_id: str,
                          labels: list):
    """
     Function Responsible for running Custom
     Form Recognizer Step

    Parameters
    ----------
    image_df : pd.DataFrame
        DataFrame, containing image infromation
    output_file: str
        File to save results to
    form_credentials : FormRecognizerPipelineSecrets
        Form recognizer credentials
    model_id: str
        The ID of the custom model being invoked
    labels: Array
        Labels or fields to extract results from
    """

    # fields to extract from custom model
    # can be tailored to whatever tags/labels the
    # custom model is trained on

    # Read in files paths
    image_paths = image_df["image"].values

    recognizer_results = []
    log.info("Computing Results...")
    for file in tqdm(image_paths):
        dict_item = {}
        dict_item["filename"] = Path(file).stem
        dict_item["results"] = run_analysis(
            endpoint=form_credentials["endpoint"],
            apim_key=form_credentials["key"],
            model_id=model_id,
            input_file=file,
        )
        recognizer_results.append(dict_item)

    text_metadata = []
    log.info("Extracting image metadata")

    for response in tqdm(recognizer_results):
        dict_item = {}
        dict_item["filename"] = response["filename"]
        dict_item["metadata"] = extract_metadata(response["results"])
        text_metadata.append(dict_item)

    # extract text items from metadata
    extracted_results = extract_text_items(
        text_metadata, labels=labels[1:]
    )

    log.info("Preparing to save results")
    # save results to csv file
    log.info(f"Result file: {output_file}")
    results_dataframe = pd.DataFrame(extracted_results)
    results_dataframe["filename"] = results_dataframe["filename"].apply(
        lambda x: x + ".jpeg"
    )
    results_dataframe.to_csv(output_file, index=False)
    log.info("Done")

    return


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
