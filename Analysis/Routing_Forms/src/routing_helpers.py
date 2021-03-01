#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from collections import Counter
import json
import os
from typing import List, Dict, Optional

import requests

from .Secrets import Secrets

def load_data(
        file_names: List[str],
        secrets: Secrets
    ) -> (List[Dict], List[str]):
    """Loads ocr results for the input file names

    :param List[str] file_names: List of files to load as the training data
    :param Secrets secrets: A configuration object that holds secrets for calling blob
        storage and the OCR endpoint

    :return List[Dict] ocr_results:List of parsed JSON responses from the OCR api. In python
        this is a dictionary corresponding to the JSON structure

    Raises:
        Exception: If the desired image is not found locally and it is in running_locally mode
    """

    ocr_results = []
    for file_name in file_names:
        if not os.path.exists(file_name):
            raise Exception(f"Provided file name does not exist: {file_name}")
        
        ocr_result = get_ocr_results(file_name, secrets.OCR_SUBSCRIPTION_KEY, secrets.OCR_ENDPOINT)

        ocr_results.append(ocr_result)
    
    return ocr_results

def get_ocr_results(
        file_name: str,
        subscription_key: str,
        ocr_url: str,
        proxies: Optional[Dict[str, str]] = None
    ) -> Dict:
    """Gets the OCR results for the given file

    If a local copy of the OCR results are already present, the code will
    load those and return quickly. Otherwise the image will be sent to the OCR 
    API endpoint. In this case the results are written to disk for easy access
    the next time.

    :param str file_name: path to the file to run OCR on
    :param str subscription_key: key for the computer vision instance
    :param str ocr_url: url for the OCR enpoint with host only.
        For example, 'https://{instance}.cognitiveservices.azure.com/'
    :param Dict[str,str] proxies: Optional set of proxies to be used on the http
        request. If none are needed, pass None

    :returns Dict[]: Parsed JSON response from the OCR service

    Raises:
        HTTPError: If the OCR response is greater than 229
    """

    ocr_url = ocr_url + "/vision/v3.1/ocr"
    result_path = f"{file_name}.json"

    # If the results already exist then we return our cached version
    if os.path.exists(result_path):
        with open(result_path) as f:
            return json.load(f)

    # Set fixed headers and parameters
    headers = {'Ocp-Apim-Subscription-Key': subscription_key, 'Content-Type': 'application/octet-stream'}
    params = {'language': 'en', 'detectOrientation': 'true'}

    # Makes sure the image is downloaded
    image_data = open(file_name, "rb").read() # Here we need the real path to the file, will exist after the previous step

    response = requests.post(ocr_url, headers=headers, params=params, data=image_data, proxies=proxies)
    print(f"OCR time: {response.elapsed}")
    
    # Throws HTTPError for bad status
    response.raise_for_status()

    results = response.json()

    # Dump cache file
    with open(result_path, "w") as f:
        json.dump(results, f)
    
    return results

def words_from_results(ocr_result: Dict) -> List[Dict]:
    """Returns the list of found words (bounding box and text)

    Note: the dictionary for each word has two fields "text" and "boundingBox",
    which represent the content and location of the extracted word respectively

    :param Dict[] ocr_results: OCR results for an image
    :returns List[Dict]:the words found in the OCR results
    """

    line_infos = [region["lines"] for region in ocr_result["regions"]]
    word_infos = []

    for line in line_infos:
        for word_metadata in line:
            for word_info in word_metadata["words"]:
                word_infos.append(word_info)

    return word_infos

def bounding_boxes_from_words(word_infos: List[Dict]) -> List[List[int]]:
    """Returns an array of arrays representing bounding boxes

    :param List[Dict] word_infos: the words found in the OCR results
    
    :returns List[List[int]]:  a list of bounding boxes ofthe found words. Each 
        entry has 4 elements aligning with [left, top, width, height]
    """
    
    bounding_boxes = []
    for word in word_infos:
        bounding_boxes.append([int(num) for num in word["boundingBox"].split(",")])
    
    return bounding_boxes

def layout_agnostic_vocabulary_vector(
        results: List[Dict],
        number_of_words: int
    ) -> List[str]:
    """Create a layout agnostic vocabulary vector

    Finds the most popular words out of a bag comprised of all layouts
    Guarantees a length based on number_of_words

    :param List[Dict] ocr_results: List of parsed JSON responses from the OCR api
    :param int number_of_words: length of the output vocabulary

    :returns List(str): list of words that make up the vocabulary
    """
    counter = Counter()
    for result in results:
        word_infos = words_from_results(result)

        for word in word_infos:
            counter.update({word["text"]: 1})

    # Create the vocabulary vector based on the most common words
    vocabulary_vector = []
    for word in counter.most_common(number_of_words):
        vocabulary_vector.append(word[0])
    
    return vocabulary_vector

def layout_aware_vocabulary_vector(
        results: List[Dict],
        number_of_words: int,
        classification_targets: List[str]
    ) -> List[str]:
    """Create a layout aware vocabulary vector

    Finds the most popular words per layout and sticks them together
    Each layout gets ceil(number_of_words/number_of_layouts) words, also repeat
    words will get removed

    :param List[Dict] ocr_results: List of parsed JSON responses from the OCR api
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
        word_infos = words_from_results(result)

        for word in word_infos:
            words[classification_target].update({word["text"]:1})

    vocabulary_vector = []
    for _, value in words.items():
        for word in value.most_common(words_per_layout):
            vocabulary_vector.append(word[0])

    # sort the output for easy check of reproducibility
    return sorted(list(set(vocabulary_vector)))