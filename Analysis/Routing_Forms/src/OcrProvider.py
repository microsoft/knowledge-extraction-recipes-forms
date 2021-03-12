#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import ABC, abstractmethod
from typing import Dict, List

from .Word import Word

class OcrProvider(ABC):

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

    @abstractmethod
    def get_raw_ocr_results(self, file_name: str) -> Dict:
        """Gets the OCR results for the given file as a Dictionary"""
        pass
    
    @abstractmethod
    def words_from_result(self, ocr_result: Dict) -> List[Word]:
        """Converts the raw dictionary result to a list of word objects"""
        pass