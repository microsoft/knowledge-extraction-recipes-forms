#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
import unittest
import os
import json
from mock import MagicMock, patch, mock_open

from shared_code import model_evaluation

@pytest.mark.evaluation
class EvaluateTest(unittest.TestCase):

    gt_path = "<ENTER GT PATH>"
    lookup_path = "./lookup_fields.json"
    predictions = "<ENTER SAMPLE EVALUATION>"

    def test_evaluate_when_all_valid(self):

        # Expecting valid output when all parameters are valid
        result = model_evaluation.evaluate(
                self.predictions,
                self.gt_path,
                self.lookup_path,
                0,0)

        assert len(result) > 0

    def test_evaluate_when_invalid_predictions_text(self):

        # Expecting invalid output when predictions are invalid
        result = model_evaluation.evaluate(
                "test",
                self.gt_path,
                self.lookup_path,
                0,0)

        assert len(result) == 0 

    def test_evaluate_when_invalid_predictions_empty(self):

        # Expecting invalid output when predictions are invalid
        result = model_evaluation.evaluate(
                [],
                self.gt_path,
                self.lookup_path,
                0,0)

        assert len(result) == 0 


    def test_evaluate_when_invalid_gt_path(self):

        # Expecting invalid output when gt path is invalid
        result = model_evaluation.evaluate(
                self.predictions,
                "test",
                self.lookup_path,
                0,0)

        assert len(result) == 0 


@pytest.mark.evaluation
class CompareTest(unittest.TestCase):

    a_text = "Hello, world!"
    b_text = "hello world"
    text_field = "Name"
    a_postalcode = "48237-2014"
    b_postalcode = "48237"
    postalcode_field = "PropertyPostalCode"
    a_money = "$3,714"
    b_money = "3714"
    money_field = "Total Amount"
    a_date = "7/8/18"
    b_date = "07/08/2018"
    date_field = "Date"

    lookup_path = "./lookup_fields.json"

    def test_compare_text_when_equal(self):

        # Expecting True when lookup_path is valid, compare method is text and a == b
        result = model_evaluation.compare(
                self.a_text,
                self.b_text,
                self.text_field,
                self.lookup_path)

        assert result == True

    def test_compare_text_when_not_equal(self):

        # Expecting False when lookup_path is valid, compare method is text and a != b
        result = model_evaluation.compare(
                self.a_text,
                "Hi there",
                self.text_field,
                self.lookup_path)

        assert result == False

    def test_compare_postalcode_when_equal(self):

        # Expecting True when lookup_path is valid, compare method is postalcode and a == b
        result = model_evaluation.compare(
                self.a_postalcode,
                self.b_postalcode,
                self.postalcode_field,
                self.lookup_path)

        assert result == True

    def test_compare_postalcode_when_not_equal(self):

        # Expecting False when lookup_path is valid, compare method is postalcode and a != b
        result = model_evaluation.compare(
                self.a_postalcode,
                "49238",
                self.postalcode_field,
                self.lookup_path)

        assert result == False

    def test_compare_money_when_equal(self):

        # Expecting True when lookup_path is valid, compare method is money and a == b
        result = model_evaluation.compare(
                self.a_money,
                self.b_money,
                self.money_field,
                self.lookup_path)

        assert result == True

    def test_compare_money_when_not_equal(self):

        # Expecting False when lookup_path is valid, compare method is money and a != b
        result = model_evaluation.compare(
                self.a_money,
                "3206",
                self.money_field,
                self.lookup_path)

        assert result == False

    def test_compare_date_when_equal(self):

        # Expecting True when lookup_path is valid, compare method is date and a == b
        result = model_evaluation.compare(
                self.a_date,
                self.b_date,
                self.date_field,
                self.lookup_path)

        assert result == True

    def test_compare_date_when_not_equal(self):

        # Expecting False when lookup_path is valid, compare method is date and a != b
        result = model_evaluation.compare(
                self.a_date,
                "09/10/2018",
                self.date_field,
                self.lookup_path)

        assert result == False

    def test_compare_date_when_wrong_compare_method(self):

        # Expecting False when lookup_path is valid, compare method is text and a == b but a and b are dates
        result = model_evaluation.compare(
                self.a_date,
                self.b_date,
                self.text_field,
                self.lookup_path)

        assert result == False

    def test_compare_date_when_invalid_lookup_path(self):

        # Expecting False when lookup_path is invalid, compare method is date and a == b
        result = model_evaluation.compare(
                self.a_date,
                self.b_date,
                self.date_field,
                "test")

        assert result == False



@pytest.mark.evaluation
class CreateEvalFileTest(unittest.TestCase):

    model_id = "abcd"
    lookup_path = "./lookup_fields.json"
    evaluation_file = "<ENTER PATH TO SAMPLE EVALUATION FILE>"
    with open(evaluation_file, 'r+') as f:
        evaluation_contents = f.read()
    evaluation = json.loads(evaluation_contents)

    ref_accuracy = 0.75

    def test_create_eval_when_all_valid(self):

        # Expecting valid output when all parameters are valid
        result,_ = model_evaluation.create_eval_file(
                self.evaluation,
                self.model_id,
                self.lookup_path)

        assert result['avgAccuracy'] > 0

    def test_create_eval_when_invalid_evaluation_text(self):

        # Expecting invalid output when evaluation is invalid (text)
        result,_ = model_evaluation.create_eval_file(
                "test",
                self.model_id,
                self.lookup_path)

        assert result['avgAccuracy'] == 0

    def test_create_eval_when_invalid_evaluation_empty(self):

        # Expecting invalid output when evaluation is invalid (empty array)
        result,_ = model_evaluation.create_eval_file(
                [],
                self.model_id,
                self.lookup_path)

        assert result['avgAccuracy'] == 0

    def test_create_eval_when_invalid_lookup_path(self):

        # Expecting lower accuracy when lookup_path is invalid
        result,_ = model_evaluation.create_eval_file(
                self.evaluation,
                self.model_id,
                "test")

        assert result['avgAccuracy'] < self.ref_accuracy


