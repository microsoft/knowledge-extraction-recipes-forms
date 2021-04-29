# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
This module utilizes a wrapper class around the Read API
that enables much easier usage of the OCR service in order to
extract text from a set of image files.
"""
import time
from typing import List
import requests
from requests.exceptions import RequestException


class ReadOCR:

    def __init__(self,
                 endpoint: str,
                 api_key: str,
                 api_version: str = "3.0",
                 language: str = "en"):

        """Constructs an instance of the ReadOCR class

        Parameters
        ----------
        endpoint: String
            Endpoint for Azure Computer Vision resource
        apim_key: String
            API key for Azure Computer Vision resource
        api_version: String
            (Optional) Version of the Read API service
            Default version is v3.0
        language: String
            (Optional) The BCP-47 language code of the text in the document.
            Currently, only English ('en'), Dutch (‘nl’), French (‘fr’),
            German (‘de’), Italian (‘it’), Portuguese (‘pt),
            and Spanish ('es') are supported.
            Default language is set to "en"
        """
        self.api_key = api_key
        self.endpoint = endpoint
        self.api_version = f"v{api_version}"
        self.language = language
        self.text_recognition_url = f"{self.endpoint}/vision/{self.api_version}/read/analyze?language={self.language}"

    def invoke_read_api(self,
                        image_data: List = None,
                        image_url: str = None,
                        filename: str = None) -> List:
        """
        Function that feeds image into the newer OCR endpoint
        (read API) and returns text results from model

        Parameters
        ----------
        image_data: Array
            (Optional) Bytes array for image file.
            Use this option if the file is used locally
        image_url: String
            (Optional) URL pointing to an uploaded image
            Use this option if the file can be accessed
            through a sharable link from within a storage container
        filename: String
            (Optional) Filename for uploaded image
             to OCR model

        Raises
        ------
        RequestException
            If the response status is not 200
        Exception
            If there is an error processing the image file

        Returns
        -------
        Array
            List containing text extracted from image.
            The Read API will extract each "line" of text identified and predicted
            as an individual string. An array containing the bounding box for the
            predicted text item will also be returned from the read model.
            Here's some sample output:

            [
             {
              'text': 'TAKE',
              'boundingBox': [78, 518, 410, 499, 412, 521, 79, 542]
              },
             {
              'text': 'ROLL',
              'boundingBox': [102, 550, 146, 548, 147, 564, 103, 566]
              },
             {
              'text': 'SCENE',
              'boundingBox': [201, 567, 544, 548, 147, 654, 123, 466]
              }
             ]

             In regards to bounding boxes, each index translates to the following position:

             [left,
              top,
              right,
              top,
              right,
              bottom,
              left,
              bottom
              ]
        """

        if image_data is None and image_url is None:
            raise TypeError("None type object error. Please Provide a valid image bytes array or file URL")

        elif image_data is not None and image_url is not None:
            raise Exception("Please provide either an image bytes array or file URL. Both items are not required.")

        elif image_data is not None:

            try:
                headers = {'Ocp-Apim-Subscription-Key': self.api_key,
                           'Content-Type': 'application/octet-stream'}

                response = requests.post(self.text_recognition_url,
                                         headers=headers,
                                         data=image_data)
                response.raise_for_status()
            except RequestException as err_msg:
                print(f"POST method failed:\n{err_msg}")

        elif image_url is not None:

            try:
                headers = {'Ocp-Apim-Subscription-Key': self.api_key}
                data = {'url': image_url}
                response = requests.post(self.text_recognition_url,
                                         headers=headers,
                                         json=data)
                response.raise_for_status()
            except RequestException as err_msg:
                print(f"POST method failed:\n{err_msg}")
                return []

        # Extracting text requires two API calls: One call to submit the
        # image for processing, the other to retrieve the text found in the image.

        # Holds the URI used to retrieve the recognized text.
        # operation_url = response.headers["Operation-Location"]

        # The recognized text isn't immediately available,
        #  so poll to wait for completion.

        analysis = {}
        poll = True
        while poll:
            try:
                response_final = requests.get(response.headers["Operation-Location"],
                                              headers=headers)
                analysis = response_final.json()
            except RequestException as err_msg:
                print(f"GET method failed:\n{err_msg}")

            # read API has a limit of 12,500 requests per hour
            # sleep reduces chances of OCR api hitting that quota
            time.sleep(1)
            if "analyzeResult" in analysis:
                poll = False
            if ("status" in analysis and analysis['status'] == 'failed'):
                poll = False

        polygons = []
        if "analyzeResult" in analysis:
            # Extract the recognized text, with bounding boxes.

            # if there is a specified filename, we can save the filename to results
            if filename is not None:
                polygons = [{
                    "filename": filename,
                    "text": line["text"],
                    "boundingBox":line["boundingBox"]
                } for line in analysis["analyzeResult"]["readResults"][0]["lines"]]

            else:
                polygons = [{"boundingBox": line["boundingBox"], "text": line["text"]}
                            for line in analysis["analyzeResult"]["readResults"][0]["lines"]]

        return polygons
