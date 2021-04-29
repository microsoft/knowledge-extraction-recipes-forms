# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Test utility functions
"""

from typing import List, Dict
import pandas as pd
import pytest
from ..utils import (
    create_df,
    compute_detection_rate)


@pytest.mark.parametrize(
    "input_dir",
    [
        ("test_data")
    ],
)
def test_create_df(input_dir) -> None:

    """
    Function that tests the create_df function

    Parameters
    ----------
    input_dir: String
        Path to the folder containing images
    """
    df = create_df(input_dir)
    assert isinstance(df, pd.DataFrame) is True


@pytest.mark.parametrize(
    "input_dir, output_dir, expected_results",
    [
        ("test_data/test_form_results",
         "test_data/test_output_dir",
         [{'video': 'video1',
           'scene_detection_rate': 0.3333333333333333,
           'take_detection_rate': 0.0},
          {'video': 'video2',
           'scene_detection_rate': 0.25,
           'take_detection_rate': 0.0},
          {'video': 'video3',
          'scene_detection_rate': 0.75,
           'take_detection_rate': 0.75}])
    ],
)
def test_compute_detection_rate(input_dir: str,
                                output_dir: str,
                                expected_results: List[Dict]) -> None:

    """
    Function that tests compute_detection_rate function

    Parameters
    ----------
    input_dir : str
        Path to the folder containing images
    output_dir: str
        Path to save output csv results to
    expected_results: Array
        Expected results from compute_detection_rate function
    """
    results = compute_detection_rate(input_dir, output_dir)
    results.sort(key=lambda item: item.get("video"))
    expected_results.sort(key=lambda item: item.get("video"))
    assert results == expected_results
