#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations
import base64
import json
from math import floor
import os
from typing import List, Dict, Any, Optional, Tuple, Union

import numpy as np
import onnxruntime as rt
from sklearn.base import BaseEstimator
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

from .WordAndLayoutEncoder import WordAndLayoutEncoder

class RoutingModel:
    """Encapsulation of routing model logic

    Attributes:
        encoder: WordAndLayoutEncoder, converts raw ocr results to feature vector
        tags: Dict[str, str], Unique identifiers for tracking where the model came from
        layouts: List[str], the layouts that are output by the model
        sklearn_model: BaseEstimator, trained sklearn model that classifies the
            encoded representation of OCR results
        onnx_model: bytes, string serialized representation of the ONNX model
        onnx_session: rt.InferenceSession, running ONNX inference session which
            makes predictions using the ONNXruntime
    """
    # For the layout encoding, we use float math to identify integer indices.
    # Due to the non-perfect representation of floats, we need to define a 
    # tolerance for equality
    TOLERANCE = 0.00001

    def __init__(
            self,
            vocabulary_vector: List[str],
            layout_shape: (int, int),
            tags: Dict[str, str] = {},
            layouts: List[str] = [], 
            sklearn_model: Optional[BaseEstimator] = None,
            onnx_model: Optional[bytes] = None
        ) -> RoutingModel:

        self.encoder = WordAndLayoutEncoder(vocabulary_vector, layout_shape)
        self.tags = tags
        self.layouts = layouts
        self.sklearn_model = sklearn_model

        if self.sklearn_model is not None:
            num_features = len(self.encoder.vocabulary_vector) + self.encoder.layout_shape[0] * self.encoder.layout_shape[1]
            input_type = [('float_input', FloatTensorType([None, num_features]))]
            
            self.onnx_model = convert_sklearn(sklearn_model, initial_types=input_type).SerializeToString()
            self.onnx_session = None
        
        elif onnx_model is not None:
            if not isinstance(onnx_model, bytes):
                self.onnx_model = onnx_model.SerializeToString()
            else:
                self.onnx_model = onnx_model

            self.onnx_session = None

    def classify_ocr_results(
            self,
            ocr_results: Dict,
            include_probability: Optional[bool] = False
        ) -> Union[str, Tuple[str, float]]:
        """Returns classified layout based on OCR results

        Acts on OCR results to assing a layout label and if include
        probability is true also the confidence in that classification.

        This method should be used after "get_ocr_results"

        :param Dict[] ocr_results: OCR results for an image
        :param bool include_probability: set to true to return the probability
        :returns str label: the classified layout
        :returns float probability: the confidence score for the classification
        """

        encoded_vector = self.encoder.encode_ocr_results(ocr_results).reshape(1, -1)

        if self.onnx_session is None:
            self.onnx_session = rt.InferenceSession(self.onnx_model)
        
        input_name = self.onnx_session.get_inputs()[0].name
        
        if include_probability:
            label_names = [ output.name for output in self.onnx_session.get_outputs() ]
            raw_prediction = self.onnx_session.run(label_names, {input_name: encoded_vector.astype(np.float32)})
            label = raw_prediction[0][0]
            probability = raw_prediction[1][0][label]
            prediction = (label, probability)
        else:
            label_names = [ self.onnx_session.get_outputs()[0].name ]
            prediction = self.onnx_session.run(label_names, {input_name: encoded_vector.astype(np.float32)})[0]

        return prediction

    def json_serialize(self, file_name: str) -> None:
        """Outputs the routing model as a json file

        :param str file_name: name of the file to write the model to
        """
        json_model = {
            "tags": self.tags,
            "layouts": self.layouts,
            "vocabulary": self.encoder.vocabulary_vector,
            "shape": self.encoder.layout_shape,
            "onnxModel": str(base64.b64encode(self.onnx_model), "utf-8")
        }
        
        with open(file_name, "w") as f:
            json.dump(json_model, f)

    @staticmethod
    def json_deserialize(model_json: str) -> RoutingModel:
        """Outputs the routing model as a json file

        :param str model_json: either name of the file to read the model from or the model itself
        
        :returns RoutingModel: class representing the loaded routing model
        """
        if model_json.startswith("{") and model_json.endswith("}"):
            data = json.loads(model_json)
        else:
            with open(model_json, "r") as f:
                data = json.load(f)
        
        tags = data.get('tags', {})
        layouts = data.get('layouts', [])
        vocabulary_vector = data['vocabulary']
        layout_shape = data['shape']
        onnx_model = base64.b64decode(data['onnxModel'].encode("utf-8"))
        
        return RoutingModel(vocabulary_vector, layout_shape, tags, layouts, onnx_model=onnx_model)
