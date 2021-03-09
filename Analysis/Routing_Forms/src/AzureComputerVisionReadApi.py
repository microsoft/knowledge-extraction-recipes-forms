import json
import os
import time
from typing import Dict, List, Optional

import requests
from .Word import Word

# Control the timing for querying for Read API results
TIMEOUT = 30
SLEEP = 1

class AzureComputerVisionReadApi:
    """Support class for Azure Computer Vision Read API

    Details on the API can be found at: https://westcentralus.dev.cognitive.microsoft.com/docs/services/computer-vision-v3-1-ga/operations/5d986960601faab4bf452005
    """
    CACHE_FILE_PATTERN = "{}.acv.read.json"
    ENDPOINT = "{}/vision/v3.1/read/analyze"

    def __init__(
            self,
            subscription_key: str,
            ocr_url: str,
            proxies: Optional[Dict[str, str]] = None
        ):
        """ Initialize a new instance of AzureComputerVisionReadApi

        :param str subscription_key: key for the computer vision instance
        :param str ocr_url: url for the OCR endpoint with host only.
            For example, 'https://{instance}.cognitiveservices.azure.com'
        :param Dict[str,str] proxies: Optional set of proxies to be used on the http
            request. If none are needed, pass None
        """

        self.subscription_key = subscription_key
        self.ocr_url = ocr_url
        self.proxies = proxies

    def get_ocr_results(
            self,
            file_name: str
        ) -> List[Word]:
        """Gets the parsed word list for the OCR results

        :param str file_name: path to the file to run OCR on
        :returns List[Word]: the words found in the OCR results
        """
        raw_results = self.get_raw_ocr_results(file_name)
        words = self.words_from_result(raw_results)

        return words

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
        params = {'language': 'en'}

        # Open the image file
        image_data = open(file_name, "rb").read()

        response = requests.post(ocr_url, headers=headers, params=params, data=image_data, proxies=self.proxies)
        result_location = response.headers['Operation-Location']

        # Throws HTTPError for bad status
        response.raise_for_status()

        tic = time.time()
        while time.time() - tic < TIMEOUT:
            time.sleep(SLEEP)
            headers = {'Ocp-Apim-Subscription-Key': self.subscription_key}

            result = requests.get(result_location, headers=headers, proxies=self.proxies)
            result.raise_for_status()

            parsed_result = result.json()

            if parsed_result['status'] == 'succeeded':
                break
            elif parsed_result['status'] == 'failed':
                raise Exception(f"Read API call failed: {json.dumps(parsed_result)}")
            
            parsed_result = None
            # Other statuses are "notStarted" and "running" in which case we go to the next iteration

        if parsed_result is None:
            raise Exception(f"Timeout of {TIMEOUT}s was exceeded waiting for Read API result")

        # Dump cache file
        with open(result_path, "w") as f:
            json.dump(parsed_result, f)
        
        return parsed_result

    def words_from_result(self, ocr_result: Dict) -> List[Word]:
        """Returns the list of found words (bounding box and text)

        Note: the dictionary for each word has two fields "text" and "boundingBox",
        which represent the content and location of the extracted word respectively

        :param Dict[] ocr_results: OCR results for an image
        :returns List[Word]: the words found in the OCR results
        """

        analyze_result = ocr_result['analyzeResult']
        words = []

        for read_result in analyze_result['readResults']: # Loop over pages
            for line in read_result['lines']:
                for word in line["words"]:
                    # Bounding box is returned in 8 number format
                    # "The eight numbers represent the four points, clockwise from the top-left corner
                    # relative to the text orientation. For image, the (x, y) coordinates are measured
                    # in pixels. For PDF, the (x, y) coordinates are measured in inches."
                    bb = word['boundingBox']
                    left = min(bb[::2])
                    top = min(bb[1::2])
                    right = max(bb[::2])
                    bottom = max(bb[1::2])

                    word_object = Word(word["text"], left, right, top, bottom)
                    words.append(word_object)

        return words