#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import json
import os
from typing import Dict, List, Optional

import requests
from .OcrProvider import OcrProvider
from .Word import Word

class AzureComputerVisionOcrApi(OcrProvider):
    """Support class for Azure Computer Vision OCR API

    Details on the API can be found at: https://westcentralus.dev.cognitive.microsoft.com/docs/services/computer-vision-v3-1-ga/operations/56f91f2e778daf14a499f20d
    """
    CACHE_FILE_PATTERN = "{}.acv.ocr.json"
    ENDPOINT = "{}/vision/v3.1/ocr"

    def __init__(
            self,
            subscription_key: str,
            ocr_url: str,
            proxies: Optional[Dict[str, str]] = None
        ):
        """ Initialize a new instance of AzureComputerVisionOcrApi

        :param str subscription_key: key for the computer vision instance
        :param str ocr_url: url for the OCR endpoint with host only.
            For example, 'https://{instance}.cognitiveservices.azure.com'
        :param Dict[str,str] proxies: Optional set of proxies to be used on the http
            request. If none are needed, pass None
        """

        self.subscription_key = subscription_key
        self.ocr_url = ocr_url
        self.proxies = proxies

    def get_raw_ocr_results(
            self, 
            file_name: str
        ) -> Dict:
        """Gets the OCR results for the given file

        If a local copy of the OCR results are already present, the code will
        load those and return quickly. Otherwise the image will be sent to the OCR 
        API endpoint. In this case the results are written to disk for easy access
        the next time.

        :param str file_name: path to the file to run OCR on

        :returns Dict[]: Parsed JSON response from the OCR service

        Raises:
            HTTPError: If the OCR response is greater than 229
        """

        ocr_url = self.ENDPOINT.format(self.ocr_url)
        result_path = self.CACHE_FILE_PATTERN.format(file_name)

        # If the results already exist then we return our cached version
        if os.path.exists(result_path):
            with open(result_path) as f:
                return json.load(f)

        # Set fixed headers and parameters
        headers = {'Ocp-Apim-Subscription-Key': self.subscription_key, 'Content-Type': 'application/octet-stream'}
        params = {'language': 'en', 'detectOrientation': 'true'}

        # Open the image file
        image_data = open(file_name, "rb").read()

        response = requests.post(ocr_url, headers=headers, params=params, data=image_data, proxies=self.proxies)
        print(f"OCR time: {response.elapsed}")
        
        # Throws HTTPError for bad status
        response.raise_for_status()

        results = response.json()

        # Dump cache file
        with open(result_path, "w") as f:
            json.dump(results, f)
        
        return results

    def words_from_result(self, ocr_result: Dict) -> List[Word]:
        """Returns the list of found words (bounding box and text)

        Note: the dictionary for each word has two fields "text" and "boundingBox",
        which represent the content and location of the extracted word respectively

        :param Dict[] ocr_results: OCR results for an image
        :returns List[Word]: the words found in the OCR results
        """

        line_infos = [region["lines"] for region in ocr_result["regions"]]
        words = []

        for line in line_infos:
            for word_metadata in line:
                for word_info in word_metadata["words"]:
                    # Each entry has 4 elements aligning with [left, top, width, height]
                    bounding_box = [int(num) for num in word_info["boundingBox"].split(",")]
                    left = bounding_box[0]
                    top = bounding_box[1]
                    right = left + bounding_box[2]
                    bottom = top + bounding_box[3]

                    word = Word(word_info["text"], left, right, top, bottom)
                    words.append(word)

        return words