# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Set of functions that leverage functions
from previous utilities and postprocessing scripts
"""

import os
from os.path import join
from pathlib import Path
from typing import List, Dict
import numpy as np
import pandas as pd
from tqdm import tqdm

from .form_recognizer_utilities import (
    run_analysis,
    extract_metadata,
    extract_text_items
)
from .custom_form_postprocessing_utilities import postprocess_form_result


def create_df(input_dir: str) -> pd.DataFrame:

    """
    Generate a pandas dataframe with columns image and video where,
    image column contains the image path, and video column contains
    the corresponding name of the video we are reading from.

    Parameters
    ----------
    input_dir : str
        Path to the folder containing images

    Returns
    -------
    pd.DataFrame
        Resulting dataframe with the following structure: image | video
    """

    data_df = pd.DataFrame(columns=["image", "video"])
    for subfolder in tqdm(os.listdir(input_dir)):
        subfolder_path = join(input_dir, subfolder)
        if os.path.isdir(subfolder_path) and subfolder.isupper():

            images = [img for img in os.listdir(subfolder_path) if Path(img).suffix == ".jpeg"]
            images_df = pd.DataFrame(
                {
                    "image": [join(subfolder, img) for img in images],
                    "video": subfolder,
                }
            )

            data_df = data_df.append(images_df)
    return data_df


def get_results(image_df: pd.DataFrame,
                output_file: str,
                endpoint: str,
                apim_key: str,
                model_id: str,
                labels: List) -> None:

    """
    Function that takes a set of images,
    before feeding as input to custom form recognizer model

    Parameters
    ----------
    image_df: pd.DataFrame
        Dataframe containing file paths
    output_file: String
        Path to save output to
    endpoint: String
        (Endpoint to form recognizer resource)
    apim_key: String
        (API key for form recognizer resource)
    model_id: String
        (ID of custom model)
    labels: String
    Set of labels used to extract metadata. Labels used
    here should match labels the custom model is trained on

    """

    # set image paths
    img_paths = image_df["image"].values

    recognizer_results = []
    for file in tqdm(img_paths):
        dict_item = {}
        dict_item["filename"] = Path(file).stem
        dict_item["results"] = run_analysis(endpoint=endpoint,
                                            apim_key=apim_key,
                                            model_id=model_id,
                                            input_file=file)
        recognizer_results.append(dict_item)

    item_metadata = []

    for response in tqdm(recognizer_results):
        dict_item = {}
        dict_item["filename"] = response["filename"]
        dict_item["metadata"] = extract_metadata(response["results"])
        item_metadata.append(dict_item)

    # extract text items from metadata
    extracted_results = extract_text_items(item_metadata,
                                           labels=labels)
    results_df = pd.DataFrame(extracted_results)
    # replace nan objects with empty strings
    df_results = results_df.replace(np.nan, '', regex=True)
    # convert all elements to string type
    df_results = df_results.applymap(str)
    df_values = df_results.to_dict(orient='records')

    # Apply Post-Processing Step
    post_processed_results = []
    for record in tqdm(df_values):
        post_processed_results.append(postprocess_form_result(record))

    post_df = pd.DataFrame(post_processed_results)
    post_df.to_csv(output_file, index=False)


def compute_detection_rate(input_dir: str,
                           output_dir: str) -> List[Dict]:

    """
    Function used to compute detection rates from
    form recognizer model. Detection rates on "scene" and
    "take" for each video will be computed

    Parameters
    ----------
    input_dir : str
        Path to the folder containing images
    output_dir: str
        Path to save output csv results to

    Returns
    -------
    Array
        Array of dict objects containing detection rates for each video
    """

    pred_dfs = []
    csv_results = []

    for fname in os.listdir(input_dir):
        if fname.endswith(".csv"):
            try:
                df = pd.read_csv(join(input_dir, fname))
                pred_dfs.append([Path(fname).stem, df])
            except pd.errors.EmptyDataError as err_msg:
                print(f"CSV File {fname} is empty, skipping over current file")
                print(err_msg)

    for item in pred_dfs:

        fname, df = item
        scene_rate = 0
        take_rate = 0
        # replace nan objects with empty strings
        df_results = df.replace(np.nan, '', regex=True)
        # convert all elements to string type
        df_results = df_results.applymap(str)
        df_values = df_results.to_dict(orient='records')

        for value in df_values:
            if len(value["scene"]) > 0 or value["scene"] != '':
                scene_rate += 1
            if len(value["take"]) > 0 or value["take"] != '':
                take_rate += 1

        scene_rate /= len(df_values)
        take_rate /= len(df_values)

        csv_results.append({
            "video": fname,
            "scene_detection_rate": scene_rate,
            "take_detection_rate": take_rate
        })

    results_df = pd.DataFrame(csv_results)
    os.makedirs(output_dir, exist_ok=True)
    results_df.to_csv(join(output_dir, "detection_rates.csv"), index=False)
    return csv_results
