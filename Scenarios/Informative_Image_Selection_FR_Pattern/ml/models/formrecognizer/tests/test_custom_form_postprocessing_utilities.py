# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Test clapperboard scoring utility functions
"""

from typing import List, Dict
import pytest
from ..custom_form_postprocessing_utilities import (
    check_roll,
    check_scene,
    check_take,
    save_to_csv)


@pytest.mark.parametrize(
    "dict_item, expected_results",
    [
        ({"scene": "", "take": "", "roll": ""},
         {"scene": "", "take": "", "roll": ""}),
        ({"scene": "30V 7", "take": "6", "roll": ""},
         {"scene": "30V 7", "take": "6", "roll": ""}),
        ({"scene": "AA18 30V 7", "take": "", "roll": ""},
         {"scene": "30V", "take": "7", "roll": "AA18"}),
        ({"scene": "179C", "take": "7", "roll": "AA18"},
         {"scene": "179C", "take": "7", "roll": "AA18"})
    ],
)
def test_check_scene(dict_item: Dict,
                     expected_results: Dict):

    """
    Function that test check_scene function

    Parameters
    ----------
    dict_item: String
        (Output from custom form model)
    expected_results: String
        (Expected result from function)
    """

    results = check_scene(dict_item)
    assert results == expected_results


@pytest.mark.parametrize(
    "dict_item, expected_results",
    [
        ({"scene": "", "take": "", "roll": ""},
         {"scene": "", "take": "", "roll": ""}),
        ({"scene": "30V 7", "take": "6", "roll": ""},
         {"scene": "30V 7", "take": "6", "roll": ""}),
        ({"scene": "", "take": "AA18 30V 7", "roll": ""},
         {"scene": "30V", "take": "7", "roll": "AA18"}),
        ({"scene": "", "take": "7 179C", "roll": "AA18"},
         {"scene": "179C", "take": "7", "roll": "AA18"})
    ],
)
def test_check_take(dict_item: Dict,
                    expected_results: Dict):

    """
    Function that test check_scene function

    Parameters
    ----------
    dict_item: String
        (Output from custom form model)
    expected_results: String
        (Expected result from function)
    """

    results = check_take(dict_item)
    assert results == expected_results


@pytest.mark.parametrize(
    "dict_item, expected_results",
    [
        ({"scene": "", "take": "", "roll": ""},
         {"scene": "", "take": "", "roll": ""}),
        ({"scene": "30V 7", "take": "6", "roll": ""},
         {"scene": "30V 7", "take": "6", "roll": ""}),
        ({"scene": "", "take": "", "roll": "AA18 30V 7"},
         {"scene": "30V", "take": "7", "roll": "AA18"}),
        ({"scene": "", "take": "7", "roll": "AA18 179C"},
         {"scene": "179C", "take": "7", "roll": "AA18"})
    ],
)
def test_check_roll(dict_item: Dict,
                    expected_results: Dict):

    """
    Function that test check_roll function

    Parameters
    ----------
    dict_item: String
        (Output from custom form model)
    expected_results: String
        (Expected result from function)
    """

    results = check_roll(dict_item)
    assert results == expected_results


@pytest.mark.parametrize(
    "target_directory, csv_file,\
    extracted_results, fieldnames",
    [

        ("postprocessed-results",
         "test-postprocessed-results.csv",
         [{"scene": "", "take": "7", "roll": "AA18 179C"},
          {"scene": "179C", "take": "7", "roll": "AA18"}],
         ["scene", "take", "roll"])
    ],
)
def test_save_to_csv(csv_file: str,
                     extracted_results: List[Dict],
                     fieldnames: List,
                     target_directory):

    """
    Function that tests save_to_csv function

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
    """

    dataframe = save_to_csv(csv_file,
                            extracted_results,
                            fieldnames,
                            target_directory=target_directory)

    assert dataframe is not None
