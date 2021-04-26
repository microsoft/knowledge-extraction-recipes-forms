# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
This script involves a set of functions that post-process
output from the custom form recognizer in order to
improve detection of scene, take, and roll elements off
clapperbaord items
"""

import os
import re
import datetime
import io
import csv
from typing import List, Dict
import pandas as pd


def clean_value(string: str) -> str:
    """
    Function that uses regex based rules to clean a
    an input string. Function removes all other
    character that are not letters or numbers

    Parameters
    ----------
    string: String
        (The string thay will be preprocessed)

    Returns
    -------
    String
        Preprocessed string
    """
    # filter out special characters
    string = re.sub(r'[^a-zA-Z0-9]', " ", string)
    # remove any extra spaces
    string = re.sub(r"\s+", " ", string)
    return string


def check_for_roll(string: str) -> bool:
    """
    Function that checks to see if clapperboard elements
    follows set of rules to be identified as a "roll" element

    Parameters
    ----------
    string: String
        (The string thay will be checked

    Returns
    -------
    Boolean
        True if object follows set of rules
        False if not.
    """

    if re.search("^[a-z]", string.lower()) and\
       re.search("[0-9]$", string.lower()) and\
       len(string) <= 5 and len(string) > 2:
        return True
    return False


def check_for_scene(string: str) -> bool:
    """
    Helper Function that checks to see if clapperboard elements
    follows set of rules to be identified as a "scene" element

    Parameters
    ----------
    string: String
        (The string thay will be checked

    Returns
    -------
    Boolean
        True if object follows set of rules
        False if not.
    """

    if re.search("^[0-9]", string.lower()) and\
       re.search("[a-z]$", string.lower()) and\
       len(string) <= 5 and len(string) > 2:
        return True
    if string.isdigit() and int(string) >= 30:
        return True
    return False


def check_for_take(string: str) -> bool:

    """
    Helper Function that checks to see if clapperboard elements
    follows set of rules to be identified as a "take" element

    Parameters
    ----------
    string: String
        (The string thay will be checked

    Returns
    -------
    Boolean
        True if object follows set of rules
        False if not.
    """

    if string.isdigit() and int(string) < 30:
        return True
    return False


def check_roll(dict_item: Dict, key: str = "roll"):

    """
    Function that performs post processing
    on custom form output in the event that most
    clapperboard items are detected and classified
    as a "roll" item

    Parameters
    ----------
    dict_item: Dict
        (Object containing output from custom
         for recognizer on a single image or item)
    key: String
        (key for item we wish to use as a means
         to preprocess data. By default key is
         set to "roll" for roll field)

    Returns
    -------
    Dict
        Post processed result
    """

    roll_string = clean_value(dict_item[key])
    values = roll_string.split(" ")
    items_to_remove = []

    if len(values) > 0:
        for item in values:
            # if we see an element that looks like a scene object and
            #  scene is empty...
            if check_for_scene(item) is True and len(dict_item["scene"]) == 0:
                # add the element to the scene tag and remove it from the roll
                #  field/array
                if item not in items_to_remove:
                    dict_item["scene"] = item
                    items_to_remove.append(item)

            # if we see an element that looks like a take object and
            #  take is empty...
            if check_for_take(item) is True and len(dict_item["take"]) == 0:
                # add the element to the take tag and remove it from
                #  the roll field/array
                if item not in items_to_remove:
                    dict_item["take"] = item
                    items_to_remove.append(item)

    # remove values that do not relate to roll artefact
    for element in items_to_remove:
        values.remove(element)

    roll_element = " ".join(values)
    dict_item[key] = roll_element
    return dict_item


def check_scene(dict_item: Dict, key: str = "scene"):

    """
    Function that performs post processing
    on custom form output in the event that most
    clapperboard items are detected and classified
    as a "scene" item

    Parameters
    ----------
    dict_item: Dict
        (Object containing output from custom
         for recognizer on a single image or item)
    key: String
        (key for item we wish to use as a means
         to preprocess data. By default key is
         set to "scene" for scene field)

    Returns
    -------
    Dict
        Post processed result
    """

    scene_string = clean_value(dict_item[key])
    values = scene_string.split(" ")
    items_to_remove = []

    if len(values) > 0:
        for item in values:
            # if we see an element that looks like a roll object and
            #  roll is empty...
            if check_for_roll(item) and len(dict_item["roll"]) == 0:
                # add the element to the scene tag and remove it from
                #  the roll field/array
                if item not in items_to_remove:
                    dict_item["roll"] = item
                    items_to_remove.append(item)

            # if we see an element that looks like a take object and take
            #  is empty...
            if check_for_take(item) and len(dict_item["take"]) == 0:
                # add the element to the scene tag and remove it from the
                #  roll field/array
                if item not in items_to_remove:
                    dict_item["take"] = item
                    items_to_remove.append(item)

    # remove items that do not apply to scene object
    for element in items_to_remove:
        values.remove(element)

    scene_element = " ".join(values)
    dict_item[key] = scene_element
    return dict_item


def check_take(dict_item: Dict, key: str = "take"):

    """
    Function that performs post processing
    on custom form output in the event that most
    clapperboard items are detected and classified
    as a "take" item

    Parameters
    ----------
    dict_item: String
        (Object containing output from custom
         for recognizer on a single image or item)
    key: String
        (key for item we wish to use as a means
         to preprocess data. By default key is
         set to "take" for take field)

    Returns
    -------
    Dict
        Post processed result
    """

    take_string = clean_value(dict_item[key])
    values = take_string.split(" ")
    items_to_remove = []

    if len(values) > 0:
        for item in values:
            # if we see an element that looks like a roll object and
            #  roll is empty...
            if check_for_roll(item) and len(dict_item["roll"]) == 0:
                # add the element to the scene tag and remove it from the
                #  roll field/array
                if item not in items_to_remove:
                    dict_item["roll"] = item
                    items_to_remove.append(item)

            # if we see an element that looks like a scene object and
            # scene is empty...
            if check_for_scene(item) and len(dict_item["scene"]) == 0:
                # add the element to the scene tag and remove it from the roll
                #  field/array
                if item not in items_to_remove:
                    dict_item["scene"] = item
                    items_to_remove.append(item)

    # remove items that do not apply to scene object
    for element in items_to_remove:
        values.remove(element)

    take_element = " ".join(values)
    dict_item[key] = take_element
    return dict_item


def postprocess_form_result(dict_item: Dict):

    """
    Function that calls check_roll,
    check_scene, check_take to perform post
    processing on custom form output

    Parameters
    ----------
    dict_item: Dict
        (Object containing output from custom
         for recognizer on a single image or item)

    Returns
    -------
    Dict
        Post processed results
    """

    dict_item = check_roll(dict_item)
    dict_item = check_scene(dict_item)
    dict_item = check_take(dict_item)
    return dict_item


def save_to_csv(csv_file: str,
                extracted_results: List[Dict],
                fieldnames: List,
                target_directory=None):

    """
    Function that serves as helper to save extracted results from OCR

    to a csv file

    Parameters
    ----------
    csv_file: String
        (The name of the CSV file data will be saved into)
    extracted_results: Array
        (Extracted results from OCR)
    fieldnames: Array
        (List of labels for clapperboard items)
    target_directory: String
        Output directory to save results. By
        default, the function assumes file will be
        saved in the same directory the script is
        invoked in.

    Returns
    -------
    Dataframe
        Object containing extracted results and
        keywords from OCR model.
    """

    if target_directory is not None:
        if not os.path.exists(target_directory):
            os.makedirs(target_directory, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H.%M.%S.%f")[:-3]
    csv_file = f"{timestamp}_{csv_file}"

    if target_directory:
        csv_file = os.path.join(target_directory,
                                csv_file)
    # write data to csv file
    with io.open(csv_file, "w", encoding="utf-8") as output_file:
        keys = fieldnames
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(extracted_results)

    return pd.DataFrame(extracted_results)
