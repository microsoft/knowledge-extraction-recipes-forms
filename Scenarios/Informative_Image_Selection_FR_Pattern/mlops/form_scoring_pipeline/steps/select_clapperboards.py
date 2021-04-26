# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Step to select clapperboards from action event using OCR(Read API)
"""

import os
from os.path import join
from pathlib import Path
from typing import Dict, List, Tuple
import logging

import click
from tqdm import tqdm
import pandas as pd
from azureml.core.run import Run

from src.utils.timestamps import get_intervals
from ml.models.readocr.get_best_clapperboard import compute_character_count
from ml.models.readocr.text_extraction import ReadOCR


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
    "--output_dir",
    type=click.STRING,
    required=True,
    help="Path to the folder to save the result in",
)
@click.option(
    "--stop_words",
    "-m",
    multiple=True,
    default=[],
    help="stop words for preprocessing involved with clapperboard selection",
)
@click.option(
    "--timestamp_interval",
    type=click.INT,
    default=1,
    help="time interval used to split clapperboards into seperate events",
)
@click.option(
    "--force",
    default=False,
    type=bool,
    help="Overwrite the results in the specified output folder",
)
def main(
    root_dir: str,
    input_dir: str,
    output_dir: str,
    stop_words: List,
    timestamp_interval: int,
    force: bool,
) -> None:
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
    stop_words: Array
        stop words that will not be counted when computing
        character level frequency
    timestamp_interval: int
        Interval used to split clapperboards into seperate events
    force: bool
        Flag that specifies whether current run
        should overwrite outputs from previous run
    """
    log.info("Clapperboard Selection Step")

    # Resolve paths
    input_dir = join(root_dir, input_dir)
    output_dir = join(root_dir, output_dir)

    run = Run.get_context()

    # convert tuple to list type
    stop_words = list(stop_words)

    log.info("Checking if output from previous run exists...")
    if os.path.exists(output_dir) and not force:
        log.info("Output path already exists, please use --force to overwrite the results. Skipping...")
        return

    # set ocr recognizer credentials
    ocr_credentials = {"key": run.get_secret("ocrkey"),
                       "endpoint": run.get_secret("ocrendpoint")}

    log.info("Beginning process to select best clapperboards..")

    # Create directory to store results in
    os.makedirs(output_dir, exist_ok=True)

    log.info("Running Clapperboard Selection Step")
    # Build dataframe
    image_obj = []
    for file in os.listdir(input_dir):
        if file.endswith(".jpeg"):
            image = file
            timestamp = int(Path(file).stem.split("=")[-1])
            image_obj.append(dict(image=image, timestamp=timestamp))

    output_file = os.path.join(output_dir, "selected_clapperboards.csv")

    image_df = pd.DataFrame(image_obj)
    image_df = image_df.sort_values(by=["timestamp"])
    image_df["image"] = image_df["image"].apply(
            lambda x: join(input_dir, x)
        )

    # feed  video dataframe into the function to select clapperboards
    _ = get_best_clapperboard(
        image_df=image_df,
        ocr_credentials=ocr_credentials,
        output_file=output_file,
        tolerance=timestamp_interval,
        stop_words=stop_words,
    )

    log.info("Finished Running Clapperboard Selection Step")


def get_best_clapperboard(
    image_df: pd.DataFrame,
    output_file: str,
    ocr_credentials: Dict,
    stop_words: List,
    tolerance: int = 1,
) -> Tuple[List, int]:
    """
    Function that uses OCR to compute
    best set of clapperboards using character level
    frequency

    Parameters
    ----------
    image_df : pd.DataFrame
        DataFrame, containing image infromation
    output_file: String
        Path to output file where results will be stored
    ocr_credentials: Dict
        Object containing credentials to invoke read API service
    stop_words: Array
        stop words that will not be counted when computing
        character level frequency
    tolerance : int, optional
        Number of neighbors we tolerate when building sequence, by default 1

    Returns
    -------
    List
        List containing path to Clapperboards
    call_count : int
        Number of calls to OCR
    """
    # array to hold best clapperboards computed for each action event
    clapperboards = []
    call_count = 0
    # check if we have an empty dataframe
    if image_df.empty:
        return clapperboards, call_count
    # get timestamp intervals dictating each action event
    intervals = get_events(df=image_df, tolerance=tolerance)

    # get images for those sets of timestamps and compute
    # best clapperboard for each event
    for event in intervals:

        # load in set of image files as byte arrays
        images = load_images(event)
        # list to store read results from OCR model for each image
        read_results = []

        # Generate Read API endpoint
        read_service = ReadOCR(endpoint=ocr_credentials["endpoint"],
                               api_key=ocr_credentials["key"])

        for image in tqdm(images):
            filename = image["filename"]
            # make API call to read model
            response = read_service.invoke_read_api(image_data=image["data"])

            # store read results
            read_results.append({"filename": filename, "results": response})
        # compute character frequency and select best clapperboard
        # char_counts is an object of type List[Tuple]
        # Here is an example of what this object looks like:
        # [(file1.jpeg, 30), file2.jpeg, 25), (file3.jpeg, 10)]
        # where tuple objects are sorted in descending order
        # clapperboard file with the highest character count will
        # selected, so char_counts[0][0] yields file1.jpeg
        char_counts = compute_character_count(read_results, stop_words=stop_words)
        if len(char_counts) > 0:
            best_clapperboard = char_counts[0][0]

            # get full path from clapperboard set
            best_clapperboard_path = None
            for path in event:
                if Path(path).stem == best_clapperboard:
                    best_clapperboard_path = Path(path).name
            clapperboards.append({"image": best_clapperboard_path})

    log.info("Preparing to save results")
    # write results to csv file
    log.info(f"Result file: {output_file}")
    pd.DataFrame(clapperboards).to_csv(output_file, index=False)
    print("Done Saving Results.")
    return clapperboards


def get_events(df: pd.DataFrame, tolerance: int = 1) -> List[List]:
    """
    Builds isolated sequences  of clapperboard
    based on the `timestamps` column. The idea is that each
    isolated sequence represents its own unique event
    Uses tolerance to determine the number of neighbors
    we tolerate when building sequence

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame, containing `timestamp` column
    tolerance : int, optional
        Number of neighbors we tolerate when building sequence, by default 1

    Returns
    -------
    List[List]
        List of clapperboards for each event
        containing first element of the detected events sequence
    """
    print(df)
    # get unique list of intervals
    set_intervals = list(set(get_intervals(df, tolerance)))
    # add max value as function excludes it
    set_intervals.append(max(df["timestamp"].values))
    set_intervals.sort()

    clapperboard_sets = []
    # get clapperboards for each event or interval
    for i in range(0, len(set_intervals) - 1):

        start = max(0, set_intervals[i] - 1)
        end = set_intervals[i + 1]
        res = df[df["timestamp"].between(start, end, inclusive=False)]
        clapperboard_sets.append(res["image"].values)

    return clapperboard_sets


def read_image_to_bytes(filename: str) -> Dict:
    """
    Function that reads in a video file as a bytes array

    Parameters
    ----------
    filename : str
        Path to image file

    Returns
    -------
    JSON
        Object containing "filename" and bytes array
    """

    with open(filename, "rb") as file:
        bytes_array = file.read()

    file_info = {}
    file_info["filename"] = Path(filename).stem
    file_info["data"] = bytes_array

    return file_info


def load_images(files: List) -> List[Dict]:
    """
    Function that reads in videos as byte arrays from a set of file paths

    Parameters
    ----------
    files: List[str]
        Array (List containing a set of file paths we
            wish to read in as byte arrays)

    Returns
    -------
    Array
        JSON objects where each object contains a filename and byte array
    """

    # if list is empty, no need in computing the rest of the function
    if len(files) == 0:
        return []

    # check if data structure is for nested files
    # nested file data structure has following structure: List[Dict]
    # where as non nested file data strcutre is: List[str]

    if isinstance(files[0], dict):
        results = []
        for element in files:
            parent = list(element.keys())[0]
            print(parent)
            images = [read_image_to_bytes(file) for file in element[parent]]
            results.append({parent: images})

        return results
    return [read_image_to_bytes(file) for file in files]


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
