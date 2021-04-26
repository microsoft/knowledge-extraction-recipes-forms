# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Test item scoring utility functions
"""

from typing import List
import pytest
from ..form_recognizer_utilities import (
    infer_type,
    extract_text_items)


@pytest.mark.parametrize(
    "input_file, expected_type",
    [
        ("test_image.jpeg", "image/jpeg"),
        ("test_image", ''),
        ("parent/directory/document.pdf", "application/pdf"),
        ("test-file.tiff", "image/tiff"),
        ("test-sample.png", "image/png"),
        ("target/new-dir/document.jpeg", "image/jpeg"),
        ("clapperboard-file.tiff", "image/tiff"),
        ("FILES/dir1/image.png", "image/png"),
        ("csv-file.csv", ''),
        ("word_document.docx", '')
    ],
)
def test_infer_type(input_file: str,
                    expected_type: str):

    """
    Function that infers the type/format of an
    input file

    to a csv file

    Parameters
    ----------
    input_file: String
        (Path to file that will be interpreted)
    expected_type: String
        (Expected result from function)
    """

    file_type = infer_type(input_file)
    assert file_type == expected_type


@pytest.mark.parametrize(
    "metadata, labels, expected_results",
    [

        ([{"metadata": None}],
         ["scene", "take"],
         []),
        ([{"metadata": {"scene": "30", "take": "7"}}],
         ["scene", "take"],
         [{"scene": "30", "take": "7"}]),
        ([{"metadata": {"roll": "AA18", "take": "7"}}],
         ["title", "director"],
         [{}])
    ],
)
def test_extract_text_items(metadata: List,
                            labels: List,
                            expected_results: List):

    """
    Function that extracts text items from
    custom form recognizer output

    Parameters
    ----------
    metadata: Array
        (Output from custom form model)
    labels: Array
        (List of labels we parse for)
    expected_results: Array
        (Expected result from function)
    """

    results = extract_text_items(metadata, labels)
    assert results == expected_results
