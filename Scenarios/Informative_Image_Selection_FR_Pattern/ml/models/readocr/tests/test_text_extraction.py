# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Test utility functions
"""

from unittest.mock import Mock, patch
import pytest
from ..text_extraction import ReadOCR


@pytest.fixture(name='text_extractor')
def fixture_text_extraction() -> ReadOCR:
    """Returns `ReadOCR` instance

    Returns
    -------
    ReadOCR
        `ReadOCR` instance
    """
    return ReadOCR("", "")


def test_text_extraction_init(text_extractor: ReadOCR):
    """Tests `ReadOCR` init

    Parameters
    ----------
    text_extractor : ReadOCR
        ReadOCR to be tested
    """
    assert text_extractor.api_key is not None
    assert text_extractor.endpoint is not None
    assert text_extractor.api_version is not None
    assert text_extractor.language is not None
    assert text_extractor.text_recognition_url is not None


@patch.object(ReadOCR, 'invoke_read_api')
def test_invoke_read_api(mock_create_transaction: Mock, text_extractor: ReadOCR):
    """Tests `invoke_read_api` function of the `ReadOCR` class

    Parameters
    ----------
    mock_create_transaction : Mock
        Mock object for `ReadOCR.invoke_read_api`
    text_extractor : ReadOCR
        `ReadOCR` class instance
    """
    mock_create_transaction.return_value = [
          {
            "boundingBox": [
              67,
              646,
              2582,
              713,
              2580,
              876,
              67,
              821
            ],
            "text": "The quick brown fox jumps"
          }]
    text_results = text_extractor.invoke_read_api(image_data=None, filename=None)
    assert mock_create_transaction.called
    assert text_results is not None
    assert isinstance(text_results, list)
