# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Test clapperboard scoring utility functions
"""

from typing import List, Dict
import pytest
from ..get_best_clapperboard import (
    compute_word_count,
    compute_character_count)


@pytest.mark.parametrize(
    "image_results, stop_words, expected_results",
    [
        ([{'filename': 'AB0001_999.jpeg',
           'results': [{'text': 'NJ'},
                       {'text': 'AA09 201B'},
                       {'text': '2'},
                       {'text': '5'},
                       {'text': '3'},
                       {'text': '5 3'}]},
         {'filename': 'AB0002_001.jpeg',
          'results': [{'text': 'SAM TUN'},
                      {'text': 'AA98 401A'},
                      {'text': 'DANNY TANGER'},
                      {'text': 'NELSON B.LIZZY'},
                      {'text': '7'}]}],

         [],

         [('AB0002_001.jpeg', 9),
          ('AB0001_999.jpeg', 8)])
    ]
)
def test_compute_word_count(image_results: List[Dict],
                            stop_words: List,
                            expected_results: List):

    """
    Function that tests compute_word_count

    Parameters
    ----------
    image_results: Dict
        (OCR results from a multiple
        clapperboard instances)
    stop_words: List
        (Once any of these stop words are hit,
         all results after these items will not
         be stored)
    expected_results: Dict
        (Expected result from function)
    """

    results = compute_word_count(image_results,
                                 stop_words)
    assert results == expected_results


@pytest.mark.parametrize(
    "image_results, stop_words, expected_results",
    [
        ([{'filename': 'AB0001_999.jpeg',
           'results': [{'text': 'NJ'},
                       {'text': 'AA09 201B'},
                       {'text': '2'},
                       {'text': '5'},
                       {'text': '3'},
                       {'text': '5 3'}]},
         {'filename': 'AB0002_001.jpeg',
          'results': [{'text': 'SAM TUN'},
                      {'text': 'AA98 401A'},
                      {'text': 'DANNY TANGER'},
                      {'text': 'NELSON B.LIZZY'},
                      {'text': '7'}]}],

         [],

         [('AB0002_001.jpeg', 39),
          ('AB0001_999.jpeg', 15)])
    ]
)
def test_compute_character_count(image_results: List[Dict],
                                 stop_words: List,
                                 expected_results: List):

    """
    Function that tests compute_word_count

    Parameters
    ----------
    image_results: Dict
        (OCR results from a multiple
        clapperboard instances)
    stop_words: List
        (Once any of these stop words are hit,
         all results after these items will not
         be stored)
    expected_results: Dict
        (Expected result from function)
    """

    results = compute_character_count(image_results,
                                      stop_words)
    assert results == expected_results
