# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
This script provides utility functions in order
to calculate clapperboard items with the
highest word/character count
"""

from typing import List, Dict


def trim_results(results: Dict,
                 stop_words: List) -> Dict:

    """
    Function used to trim results from OCR model
    will stop storing words or results after stop
    word is hit.

    Parameters
    ----------
    results: Dict
        (OCR results from a clapperboard instance)
    stop_words: List
        (Once any of these stop words are hit,
         all results after these items will not
         be stored)

    Returns
    -------
    Dict
        Truncated results from OCR model
    """

    idx = 0
    filtered_res = []
    flag = True

    while idx < len(results):
        for element in stop_words:
            if element.lower() in results[idx]["text"].lower():
                flag = False
                break

        if flag is False:
            break

        filtered_res.append(results[idx])
        idx += 1

    return filtered_res


def word_count_helper(results: Dict) -> int:

    """
    Helper Function that computes
    word count for ocr results on a single image

    Parameters
    ----------
    results: Dict
        (OCR results from a clapperboard instance)

    Returns
    -------
    Int
        Number of words computed from
        OCR results
    """

    count = 0
    for element in results:
        words_list = element["text"].split(" ")
        count += len(words_list)
    return count


def character_count_helper(results: Dict) -> int:

    """
    Helper Function that computes
    character count for ocr results on a single image

    Parameters
    ----------
    results: Dict
        (OCR results from a clapperboard instance)

    Returns
    -------
    Int
        Number of words computed from
        OCR results
    """

    count = 0
    for element in results:
        words_list = element["text"].split(" ")
        for word in words_list:
            count += len(word)
    return count


def compute_word_count(image_results: List,
                       stop_words: List) -> List:

    """
    Function that computes  word count
    for ocr results on a set of images

    Parameters
    ----------
    image_results: Array
        (OCR results from a multiple
        clapperboard instances)
    stop_words: List
        (Once any of these stop words are hit,
         all results after these items will not
         be stored)

    Returns
    -------
    List
        Sorted object containing images
        with highest word count in descending order
    """

    results = {}

    for element in image_results:
        filename = element["filename"]
        ocr_results = element["results"]
        trimmed_results = trim_results(ocr_results,
                                       stop_words)
        results[filename] = word_count_helper(trimmed_results)

    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    return sorted_results


def compute_character_count(image_results: List,
                            stop_words: List) -> List:

    """
    Function that computes  character count
    for ocr results on a set of images

    Parameters
    ----------
    image_results: Array
        (OCR results from a multiple
        clapperboard instances)
    stop_words: List
        (Once any of these stop words are hit,
         all results after these items will not
         be stored)

    Returns
    -------
    List
        Sorted object containing images
        with highest character count in descending order
    """

    results = {}

    for element in image_results:
        filename = element["filename"]
        ocr_results = element["results"]
        trimmed_results = trim_results(ocr_results,
                                       stop_words)
        results[filename] = character_count_helper(trimmed_results)

    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    return sorted_results
