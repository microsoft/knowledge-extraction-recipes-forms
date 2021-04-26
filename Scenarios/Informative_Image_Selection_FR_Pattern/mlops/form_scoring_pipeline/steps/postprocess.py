# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Step to apply postprocessing on output from
custom form recognizer model
"""

import os
from os.path import join
import logging
import click
from tqdm import tqdm
import numpy as np
import pandas as pd

from ml.models.formrecognizer.custom_form_postprocessing_utilities import (
    postprocess_form_result,
)

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
    "--output_dir",
    type=click.STRING,
    required=True,
    help="Path to the folder to save the result in",
)
@click.option(
    "--force",
    default=False,
    type=bool,
    help="Overwrite the results in the specified output folder",
)
def main(root_dir: str, input_dir: str, output_dir: str, force: bool) -> None:
    """
    Main function for receiving args, and passing them through to form recognizer postprocessing function

    Parameters
    ----------
    root_dir: str
        Root datastore being used
    input_dir: str
        Directory containing input data
    output_dir: str
        Path to save outputs to
    force: bool
        Flag that specifies whether current run
        should overwrite outputs from previous run
    """

    log.info("Form Recognizer Postporcessing Step")

    # Resolve paths
    input_dir = join(root_dir, input_dir, "form_results")
    output_dir = join(root_dir, output_dir, "postprocessed_form_results")

    log.info("Checking if output from previous run exists...")
    if os.path.exists(output_dir) and not force:
        log.info("Output path already exists, please use --force to overwrite the results. Skipping...")
        return

    # Create directory to store results in
    os.makedirs(output_dir, exist_ok=True)

    log.info("Running Postprocessing Step...")
    # Processing videos
    for file in os.listdir(input_dir):
        form_results = pd.read_csv(join(input_dir, file))
        output_file = os.path.join(output_dir, file)

        run_postprocessing(image_df=form_results, output_file=output_file)

    log.info("Finished Running Form Recognizer Postprocessing Step.")


def run_postprocessing(image_df: pd.DataFrame, output_file: str) -> None:
    """
    Function Responsible for running postprocessing Step
    will apply rule based corrections on
    possible errors form recognizer could have made

    Parameters
    ----------
    image_df : pd.DataFrame
        DataFrame, containing image infromation
    output_file: String
        Path to output file where results will be stored
    """

    log.info("Preparing results for postprocessing...")
    # replace nan objects with empty strings
    df_results = image_df.replace(np.nan, "", regex=True)
    # convert all elements to string type
    df_results = df_results.applymap(str)
    # convert results to list of dict
    df_values = df_results.to_dict(orient="records")

    # Apply Post-Processing Step
    log.info("Applying postprocessing step on results...")
    post_processed_results = []

    log.info("Postprocessing starting...")
    for record in tqdm(df_values):
        post_processed_results.append(postprocess_form_result(record))

    # save results to csv file
    log.info("Preparing to save results")
    results_dataframe = pd.DataFrame(post_processed_results)
    save_results(output_file=output_file, results_df=results_dataframe)
    log.info("Done")


def save_results(output_file: str, results_df: pd.DataFrame) -> None:
    """
    Function Responsible saving form recognizer results

    Parameters
    ----------
    output_file: String
        Path to output file where results will be stored
    results_df: pd.DataFrame
        Dataframe containing form recognizer results
    """
    # replace column name for filename field
    results_df = results_df.rename(columns={"filename": "image-file"})
    # save full form recognizer results
    results_df.to_csv(output_file, index=False)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
