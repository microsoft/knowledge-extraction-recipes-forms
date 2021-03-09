#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from collections import Counter
import json
import os
from typing import List, Dict, Optional, Union

import requests

from .Secrets import Secrets
from .Word import Word

def load_data(
        file_names: List[str],
        ocr_provider,
        raw=False
    ) -> Union[List[Dict], List[List[Word]]]:
    """Loads ocr results for the input file names

    If the raw parameter is True, it will return a list of dictionaries representing the OCR
    results from each image. Otherwise it will extract the detected words form the OCR result and
    for each image return a list of Word objects, which include the text and location.

    :param List[str] file_names: List of files to load as the training data
    :param Secrets secrets: A configuration object that holds secrets for calling blob
        storage and the OCR endpoint

    :return Union[List[Dict], List[Word]) ocr_results: If raw is True, list of parsed JSON
        responses from the OCR api. Otherwise it returns a List of lists of Words, where the
        first index is the image number and the second is the word within that image.
    Raises:
        Exception: If the desired image is not found locally and it is in running_locally mode
    """

    ocr_results = []
    for file_name in file_names:
        if not os.path.exists(file_name):
            raise Exception(f"Provided file name does not exist: {file_name}")
        
        ocr_result = ocr_provider.get_ocr_results(file_name)
        if not raw:
            ocr_result = ocr_provider.words_from_result(ocr_result)

        ocr_results.append(ocr_result)
    
    return ocr_results

def layout_agnostic_vocabulary_vector(
        results: List[List[Word]],
        number_of_words: int
    ) -> List[str]:
    """Create a layout agnostic vocabulary vector

    Finds the most popular words out of a bag comprised of all layouts
    Guarantees a length based on number_of_words

    :param List[List[Word]] ocr_results: List of List of words found in each image
    :param int number_of_words: length of the output vocabulary

    :returns List(str): list of words that make up the vocabulary
    """
    counter = Counter()
    for result in results:
        for word in result:
            counter.update({word.text: 1})

    # Create the vocabulary vector based on the most common words
    vocabulary_vector = []
    for word in counter.most_common(number_of_words):
        vocabulary_vector.append(word[0])
    
    return vocabulary_vector

def layout_aware_vocabulary_vector(
        results: List[List[Word]],
        number_of_words: int,
        classification_targets: List[str]
    ) -> List[str]:
    """Create a layout aware vocabulary vector

    Finds the most popular words per layout and sticks them together
    Each layout gets ceil(number_of_words/number_of_layouts) words, also repeat
    words will get removed

    :param List[List[Word]] ocr_results: List of List of words found in each image
    :param int number_of_words: length of the output vocabulary
    :param List[str] classification_targets: list of layout per set of OCR results
        to be used for grouping similar layouts

    :returns List(str): list of words that make up the vocabulary
    """
    unique_layouts = list(set(classification_targets))
    words_per_layout = int(number_of_words / len(unique_layouts) + 1)
    
    words = {}
    for layout in unique_layouts:
        words[layout] = Counter()
    
    for result, classification_target in zip(results, classification_targets):
        for word in result:
            words[classification_target].update({word.text:1})

    vocabulary_vector = []
    for _, value in words.items():
        for word in value.most_common(words_per_layout):
            vocabulary_vector.append(word[0])

    # sort the output for easy check of reproducibility
    return sorted(list(set(vocabulary_vector)))