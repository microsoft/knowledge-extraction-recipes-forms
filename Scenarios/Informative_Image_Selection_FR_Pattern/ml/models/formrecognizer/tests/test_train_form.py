# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Test utility functions
"""

from unittest.mock import Mock, patch
import pytest
from ..train_form import TrainFormRecognizer


@pytest.fixture(name='train_form_recognizer')
def fixture_train_form_recognizer() -> TrainFormRecognizer:
    """Returns `TrainFormRecognizer` instance

    Returns
    -------
    TrainFormRecognizer
        `TrainFormRecognizer` instance
    """
    return TrainFormRecognizer("", "")


def test_train_form_recognizer_init(train_form_recognizer: TrainFormRecognizer):
    """Tests `TrainFormRecognizer` init

    Parameters
    ----------
    train_form_recognizer : TrainFormRecognizer
        TrainFormRecognizer to be tested
    """
    assert train_form_recognizer.apim_key is not None
    assert train_form_recognizer.endpoint is not None


@patch.object(TrainFormRecognizer, 'train_custom_model')
def test_train_custom_model(mock_create_transaction: Mock, train_form_recognizer: TrainFormRecognizer):
    """Tests `train_custom_model` function of the `TrainFormRecognizer` class

    Parameters
    ----------
    mock_create_transaction : Mock
        Mock object for `TrainFormRecognizer.train_custom_model`
    train_form_recognizer : TrainFormRecognizer
        `TrainFormRecognizer` class instance
    """
    mock_create_transaction.return_value = "https://sample/get-url.azure.com"
    get_url = train_form_recognizer.train_custom_model(source="",
                                                       prefix="")
    assert mock_create_transaction.called
    assert get_url is not None


@patch.object(TrainFormRecognizer, 'get_train_results')
def test_get_train_results(mock_create_transaction: Mock, train_form_recognizer: TrainFormRecognizer):
    """Tests `get_train_results` function of the `TrainFormRecognizer` class

    Parameters
    ----------
    mock_create_transaction : Mock
        Mock object for `TrainFormRecognizer.get_train_results`
    train_form_recognizer : TrainFormRecognizer
        `TrainFormRecognizer` class instance
    """
    mock_create_transaction.return_value = dict()
    train_results = train_form_recognizer.get_train_results(get_url="")
    assert mock_create_transaction.called
    assert isinstance(train_results, dict)
