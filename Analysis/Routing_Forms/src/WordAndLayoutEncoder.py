#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations
import os
from math import floor
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np

from .routing_helpers import words_from_results, bounding_boxes_from_words

class WordAndLayoutEncoder:
    """Encapsulation of word and layout based encoding logic

    Attributes:
        vocabulary_vector: List[str], the vocabulary words that should be used
            for word encoding
        layout_shape: (int, int), shape for the layout encoding
    """
    # For the layout encoding, we use float math to identify integer indices.
    # Due to the non-perfect representation of floats, we need to define a 
    # tolerance for equality
    TOLERANCE = 0.00001

    def __init__(
            self,
            vocabulary_vector: List[str],
            layout_shape: (int, int),
        ) -> WordAndLayoutEncoder:

        self.vocabulary_vector = vocabulary_vector
        self.layout_shape = layout_shape

    def encode_ocr_results(self, ocr_results: Dict) -> np.ndarray:
        """Encodes the OCR results into a vector that can be classified

        :param Dict[] ocr_results: OCR results for an image
        :returns np.ndarray encoding: encoded representation of the OCR results
        """

        word_infos = words_from_results(ocr_results)
        word_encoding = self.evaluate_word_vector(word_infos)

        bounding_boxes = bounding_boxes_from_words(word_infos)
        layout_encoding = self.encode_bounding_boxes(bounding_boxes).flatten()

        return np.concatenate((word_encoding, layout_encoding), axis=0)

    def evaluate_word_vector(
            self,
            word_infos: List[Dict]
        ) -> np.ndarray:
        """Returns a vector the same size as self.vocabulary_vector with a 1 if the
        word is present and a 0 otherwise

        :param List[Dict] word_infos: the words found in the OCR results
        
        :returns np.ndarray: binary word count encoding of the input words against the word vector
        """

        score = np.zeros(len(self.vocabulary_vector))

        for word_info in word_infos:
            if word_info["text"] in self.vocabulary_vector:
                index = self.vocabulary_vector.index(word_info["text"])
                score[index] = 1
        return score
    
    def encode_bounding_boxes(
            self,
            boxes: List[List[int]]
        ) -> np.ndarray:
        """Encodes bounding box information into array of new_size

        :param List[List[int]] boxes: a list of bounding boxes of the found words.
            Each entry has 4 elements aligning with [left, top, width, height]
        
        :returns np.ndarray encoding: location encoding for the OCR results
        """

        # Initialize counters to find the crop box
        top = 100000
        bottom = 0
        left = 100000
        right = 0

        for box in boxes:
            # Finding the crop box
            top = min(box[1], top)
            bottom = max(box[1]+box[3], bottom)
            left = min(box[0], left)
            right = max(box[0]+box[2], right)

        # Now that we have the external crop box that holds all of the bounding
        # boxes we can scale that crop to self.layout_shape and embed the locations
        result = np.zeros(self.layout_shape)

        # Scalers to project the outside of the bounding box to the outside of 
        # the new array
        horizontal_scaler = (self.layout_shape[1] - 1) / (right - left)
        vertical_scaler = (self.layout_shape[0] - 1) / (bottom - top)

        for box in boxes:
            scaled_top = (box[1] - top) * vertical_scaler
            scaled_left = (box[0] - left) * horizontal_scaler
            scaled_bottom = (box[1] + box[3] - top) * vertical_scaler
            scaled_right = (box[0] + box[2] - left) * horizontal_scaler

            # Indices for the boxes that we are going to affect
            top_index = floor(scaled_top)
            left_index = floor(scaled_left)

            # Tolerance is to handle float errors
            bottom_index = floor(scaled_bottom + self.TOLERANCE)
            right_index = floor(scaled_right + self.TOLERANCE)

            # Percent of index that is represented by the bounding box
            top_scaler = (top_index + 1) - scaled_top
            left_scaler = (left_index + 1) - scaled_left
            bottom_scaler = scaled_bottom - bottom_index
            right_scaler = scaled_right - right_index

            # Correction for float errors
            if bottom_scaler <= self.TOLERANCE: bottom_scaler = 1
            if right_scaler <= self.TOLERANCE: right_scaler = 1
            
            for ix in range(top_index, bottom_index + 1):
                for iy in range(left_index, right_index + 1):
                    value = 1
                    if ix == top_index: value *= top_scaler
                    if ix == bottom_index: value *= bottom_scaler
                    if iy == left_index: value *= left_scaler
                    if iy == right_index: value *= right_scaler

                    result[ix,iy] += value

        return result
