#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
import unittest
import os
import json
from mock import MagicMock, patch, mock_open

from shared_code import autolabeling
from shared_code import utils

@pytest.mark.autolabeling
class FindAnchorKeysTest(unittest.TestCase):

    gt_path = "<ENTER GT PATH>"
    gt_df = utils.load_excel(gt_path)
    file_name = "<ENTER FILE NAME>"
    ocr_file = "<ENTER PATH TO OCR FILE>"
    with open(ocr_file, 'r+') as f:
        ocr_contents = f.read()
    analyze_result = json.loads(ocr_contents)
    key_field_names = ['Date', 'Name']
    lookup_path = "./lookup_fields.json"


    def test_find_anchor_keys_in_invoice_when_valid(self):
    
        # Expecting valid output when all parameters are valid
        result = autolabeling.find_anchor_keys_in_invoice(
                self.gt_df,
                self.file_name,
                self.analyze_result,
                self.key_field_names,
                self.lookup_path)

        assert len(result[self.file_name]) > 0 

    def test_find_anchor_keys_in_invoice_when_invalid_gt(self):

        # Expecting invalid output when the ground truth is not provided
        result = autolabeling.find_anchor_keys_in_invoice(
                None,
                self.file_name,
                self.analyze_result,
                self.key_field_names,
                self.lookup_path)

        assert len(result[self.file_name]) == 0 

    def test_find_anchor_keys_in_invoice_when_invalid_filename(self):

        # Expecting invalid output when the file name is wrong
        result = autolabeling.find_anchor_keys_in_invoice(
                self.gt_df,
                "test.pdf",
                self.analyze_result,
                self.key_field_names,
                self.lookup_path)

        assert len(result["test.pdf"]) == 0 

    def test_find_anchor_keys_in_invoice_when_invalid_lookup_path(self):
    
        # Expecting invalid output when the lookup file is wrong
        result = autolabeling.find_anchor_keys_in_invoice(
                self.gt_df,
                self.file_name,
                self.analyze_result,
                self.key_field_names,
                "test.json")

        assert len(result[self.file_name]) == 0 

    def test_find_anchor_keys_in_invoice_when_invalid_ocr(self):
    
        # Expecting invalid output when the ocr file is wrong
        result = autolabeling.find_anchor_keys_in_invoice(
                self.gt_df,
                self.file_name,
                "test.json",
                self.key_field_names,
                self.lookup_path)

        assert len(result[self.file_name]) == 0 

    def test_find_anchor_keys_in_invoice_when_no_fields(self):
    
        # Expecting invalid output when there are no fields
        result = autolabeling.find_anchor_keys_in_invoice(
                self.gt_df,
                self.file_name,
                self.analyze_result,
                [],
                self.lookup_path)

        assert len(result[self.file_name]) == 0 

@pytest.mark.autolabeling
class MapColumnsTest(unittest.TestCase):

    key_name = 'Date'
    lookup_path = "./lookup_fields.json"

    def test_map_columns_when_valid(self):
    
        # Expecting valid output when all parameters are valid
        result = autolabeling.map_columns(self.key_name, self.lookup_path)

        assert len(result) > 0 

    def test_map_columns_when_invalid_lookup_path(self):
    
        # Expecting invalid output when lookup file is wrong
        result = autolabeling.map_columns(self.key_name, "test.json")

        assert len(result) == 0

    def test_map_columns_when_invalid_field(self):
    
        # Expecting invalid output when field doesn't exist
        result = autolabeling.map_columns("Test", self.lookup_path)

        assert len(result) == 0

@pytest.mark.autolabeling
class LookupCompareTest(unittest.TestCase):

    column_name = 'Total Amount'
    lookup_path = "./lookup_fields.json"

    def test_lookup_compare_when_valid(self):
    
        # Expecting valid output when all parameters are valid
        result = autolabeling.lookup_compare(self.column_name, self.lookup_path)

        assert result == 'money'

    def test_lookup_compare_when_invalid_lookup_path(self):
    
        # Expecting valid output when all parameters are valid
        result = autolabeling.lookup_compare(self.column_name, "test.json")

        assert result == ''

    def test_lookup_compare_when_invalid_column(self):
    
        # Expecting invalid output when column doesn't exist
        result = autolabeling.lookup_compare("Test", self.lookup_path)

        assert result == ''

@pytest.mark.autolabeling
class MatchBboxTest(unittest.TestCase):

    line_match1 =  {"language": "en", 
                "boundingBox": [7.9933, 10.6344, 8.28, 10.6344, 8.28, 10.7211, 7.9933, 10.7211], 
                "text": "3,156.05", 
                "words": [{"boundingBox": [7.9971, 10.6351, 8.2792, 10.6371, 8.279, 10.722, 7.9963, 10.7244], 
                    "text": "180.56", "confidence": 0.958}
                ]}
    line_match2 = {
                "language": "en",
                "boundingBox": [0.6069, 1.4333, 2.2641, 1.4433, 2.2641, 1.5667, 0.6069, 1.5567],
                "text": "Total1 $180.56",
                "words": [{
                    "boundingBox": [0.613, 1.4362, 1.5279, 1.4416, 1.5284, 1.5663, 0.6109, 1.5555],
                    "text": "Total1",
                    "confidence": 0.955
                }, {
                    "boundingBox": [1.5514, 1.4417, 2.2474, 1.4464, 2.2498, 1.5687, 1.5519, 1.5665],
                    "text": "$180.56",
                    "confidence": 0.947
                }]
                }
    line_match3 = {
                "language": "en",
                "boundingBox": [4.955, 3.0733, 7.1157, 3.08, 7.1123, 3.21, 4.955, 3.1933],
                "text": "LOS ANGELES CA 90079-6279",
                "words": [{
                    "boundingBox": [4.9568, 3.0767, 5.5256, 3.0749, 5.5251, 3.1989, 4.9563, 3.1902],
                    "text": "LOS",
                    "confidence": 0.911
                }, {
                    "boundingBox": [5.5851, 3.0748, 6.1651, 3.076, 6.1646, 3.2061, 5.5846, 3.1998],
                    "text": "ANGELES",
                    "confidence": 0.959
                }, {
                    "boundingBox": [6.2023, 3.0762, 6.3807, 3.0773, 6.3802, 3.2079, 6.2017, 3.2065],
                    "text": "CA",
                    "confidence": 0.873
                }, {
                    "boundingBox": [6.403, 3.0774, 7.1094, 3.0841, 7.1088, 3.21, 6.4025, 3.208],
                    "text": "90079-6279",
                    "confidence": 0.937
                }]
            }

    line_match4 = {
                "language": "en",
                "boundingBox": [4.955, 3.0733, 7.1157, 3.08, 7.1123, 3.21, 4.955, 3.1933],
                "text": "LOS ANGELES CA 90079 6279",
                "words": [{
                    "boundingBox": [4.9568, 3.0767, 5.5256, 3.0749, 5.5251, 3.1989, 4.9563, 3.1902],
                    "text": "LOS",
                    "confidence": 0.911
                }, {
                    "boundingBox": [5.5851, 3.0748, 6.1651, 3.076, 6.1646, 3.2061, 5.5846, 3.1998],
                    "text": "ANGELES",
                    "confidence": 0.959
                }, {
                    "boundingBox": [6.2023, 3.0762, 6.3807, 3.0773, 6.3802, 3.2079, 6.2017, 3.2065],
                    "text": "CA",
                    "confidence": 0.873
                }, {
                    "boundingBox": [6.403, 3.0774, 7.1094, 3.0841, 7.1088, 3.21, 6.4025, 3.208],
                    "text": "90079",
                    "confidence": 0.937
                }, {
                    "boundingBox": [7.403, 3.0774, 8.1094, 3.0841, 8.1094, 3.21, 7.403, 3.208],
                    "text": "6279",
                    "confidence": 0.937
                }]
            }
    line_nomatch = {
                "language": "en",
                "boundingBox": [4.3114, 2.5167, 4.7382, 2.52, 4.7382, 2.63, 4.3081, 2.6267],
                "text": "Ship To:",
                "words": [{
                    "boundingBox": [4.3166, 2.5195, 4.5491, 2.5255, 4.5495, 2.6325, 4.3146, 2.6302],
                    "text": "Ship",
                    "confidence": 0.959
                }, {
                    "boundingBox": [4.5782, 2.5255, 4.7344, 2.5252, 4.7368, 2.6294, 4.5789, 2.632],
                    "text": "To:",
                    "confidence": 0.909
                }]
            }
    gt_processed1 = ["3156.05"]
    gt_processed2 = ["180.56"]
    gt_processed3 = ["los angeles", "ca", "90079"]
    compare_methods1 = ['money']
    compare_methods2 = ['city', 'state', 'postalCode']

    def test_match_bbox_line_level_one_column_when_line_equal(self):
    
        # Expecting match at line level when the line is equal to the value and there's only one column to look at
        result,_,_ = autolabeling.match_bbox(self.line_match1, "", self.gt_processed1, self.compare_methods1, False)

        assert result == True
    
    def test_match_bbox_line_level_one_column_when_line_contains(self):
    
        # Expecting no match at line level when the line only contains the value and there's only one column to look at
        result,_,_ = autolabeling.match_bbox(self.line_match2, "", self.gt_processed2, self.compare_methods1, False)

        assert result == False

    def test_match_bbox_word_level_one_column_when_line_contains(self):
    
        # Expecting match at word level when the line contains the value and there's only one column to look at
        result,_,_ = autolabeling.match_bbox(self.line_match2, "", self.gt_processed2, self.compare_methods1, True)

        assert result == True

    def test_match_next_line_one_column_when_next_line_contains(self):
    
        # Expecting match at line level when the next line is equal to the value and there's only one column to look at
        result,_,_ = autolabeling.match_bbox(self.line_nomatch, self.line_match1, self.gt_processed1, self.compare_methods1, True)

        assert result == True

    def test_match_bbox_line_level_several_columns_when_line_equal(self):
    
        # Expecting match at line level when the line is equal to the value and there are several columns to look at
        result,_,_ = autolabeling.match_bbox(self.line_match3, "", self.gt_processed3, self.compare_methods2, False)

        assert result == True

    def test_match_bbox_line_level_several_columns_when_line_contains(self):
    
        # Expecting no match at line level when the line only contains the value and there are several columns to look at
        result,_,_ = autolabeling.match_bbox(self.line_match4, "", self.gt_processed3, self.compare_methods2, False)

        assert result == False

    def test_match_bbox_word_level_several_columns_when_line_contains(self):
    
        # Expecting match at word level when the line contains the value and there are several columns to look at
        result,_,_ = autolabeling.match_bbox(self.line_match4, "", self.gt_processed3, self.compare_methods2, True)

        assert result == True

    def test_match_bbox_when_no_match(self):

        # Expecting no match at word level when the line and next line are not a match
        result,_,_ = autolabeling.match_bbox(self.line_nomatch, self.line_nomatch, self.gt_processed1, self.compare_methods1, True)

        assert result == False

    def test_match_bbox_when_wrong_compare_methods(self):

        # Expecting no match at word level when the compare method is wrong
        result,_,_ = autolabeling.match_bbox(self.line_match3, "", self.gt_processed3, self.compare_methods1, True)

        assert result == False


@pytest.mark.autolabeling
class AdjustBboxTest(unittest.TestCase):

    # Original bbox
    bbox1 = [4, 2, 5, 2, 5, 3, 4, 3]
    # Bbox to the right of original bbox
    bbox2 = [6, 2, 7, 2, 7, 3, 6, 3]
    # Bbox inside original bbox
    bbox3 = [4.5, 2, 4.8, 2, 4.8, 3, 4.8, 3]
    # Bbox on top of original bbox
    bbox4 = [4, 4, 5, 4, 5, 5, 4, 5]

    def test_adjust_bbox_when_to_right(self):
    
        # Expecting bbox to adjust to include new bbox
        result = autolabeling.adjust_bbox(self.bbox1, self.bbox2)

        assert result == [4, 2, 7, 2, 7, 3, 4, 3]

    def test_adjust_bbox_when_inside(self):
    
        # Expecting bbox to adjust to include new bbox
        result = autolabeling.adjust_bbox(self.bbox1, self.bbox3)

        assert result == self.bbox1

    def test_adjust_bbox_when_on_top(self):
    
        # Expecting bbox to adjust to include new bbox
        result = autolabeling.adjust_bbox(self.bbox1, self.bbox4)

        assert result == [4, 2, 5, 2, 5, 5, 4, 5]

    def test_return_same_when_original_bbox_bad_format(self):

        # Expecting same result when the format of the original bbox is bad
        result = autolabeling.adjust_bbox("test", self.bbox2)

        assert result == "test"

    def test_return_same_when_new_bbox_bad_format(self):

        # Expecting same result when the format of the original bbox is bad
        result = autolabeling.adjust_bbox(self.bbox1, "test")

        assert result == self.bbox1


@pytest.mark.autolabeling
class GetTemplatesTest(unittest.TestCase):

    doc_name_valid = "test.pdf"
    doc_name_invalid = None
    field_name = "test"

    def test_get_label_file_template_when_valid(self):
    
        # Expecting label file template when doc name valid
        result = autolabeling.get_label_file_template(self.doc_name_valid)

        assert result['document'] == self.doc_name_valid

    def test_get_label_file_template_when_doc_name_invalid(self):
    
        # Expecting label file template when doc name valid
        result = autolabeling.get_label_file_template(self.doc_name_invalid)

        assert result == None

    def test_get_field_template(self):
    
        # Expecting field template back
        result = autolabeling.get_field_template(self.field_name)

        assert result['label'] == self.field_name

    def test_get_value_template(self):
    
        # Expecting value template back
        result = autolabeling.get_value_template("test", "test", "test")

        assert len(result) > 0


@pytest.mark.autolabeling
class CreateLabelsTest(unittest.TestCase):

    gt_path = "<ENTER GT PATH>"
    file_path = "<ENTER FILE PATH>"
    file_name = "<ENTER FILE NAME>"
    ocr_file = "<ENTER PATH TO OCR FILE>"

    with open(ocr_file, 'r+') as f:
        ocr_contents = f.read()
    analyze_result = json.loads(ocr_contents)
    key_field_names = ['Date', 'Total Amount']
    lookup_path = "./lookup_fields.json"
    ocr_boundingbox = [4.0, 2.0, 7.0, 2.0, 7.0, 3.0, 4.0, 3.0]
    page, height, width = 1, 920, 1080
    key_field_details = [{"Date": "02/08/18", "page": page, "height": width, "width": width, "BoundingBox": ocr_boundingbox}, 
                        {"Total Amount": "3214", "page": page, "height": height, "width": width, "BoundingBox": ocr_boundingbox}]
    keys = {}
    keys[file_name] = []
    found_keys = []
    key = 'Date'
    ocr_text = "02/08/18"

    def test_analyze_labels_when_valid(self):
    
        # Expecting success when all parameters are valid
        result,_ = autolabeling.analyze_labels(
            self.gt_path,
            self.file_path,
            self.analyze_result,
            self.key_field_names,
            self.lookup_path)

        assert result != None

    def test_analyze_labels_when_gt_path_invalid(self):
    
        # Expecting failure when gt path is invalid
        result,_ = autolabeling.analyze_labels(
            "test",
            self.file_path,
            self.analyze_result,
            self.key_field_names,
            self.lookup_path)

        assert result == None

    def test_analyze_labels_when_file_name_invalid(self):
    
        # Expecting failure when file name is invalid
        result,_ = autolabeling.analyze_labels(
            self.gt_path,
            [],
            self.analyze_result,
            self.key_field_names,
            self.lookup_path)

        assert result == None

    def test_analyze_labels_when_analyze_result_invalid(self):
    
        # Expecting failure when analyze result is invalid
        result,_ = autolabeling.analyze_labels(
            self.gt_path,
            self.file_path,
            None,
            self.key_field_names,
            self.lookup_path)

        assert len(result['labels']) == 0

    def test_analyze_labels_when_key_field_names_invalid(self):
    
        # Expecting failure when key field names is invalid
        result,_ = autolabeling.analyze_labels(
            self.gt_path,
            self.file_path,
            self.analyze_result,
            "",
            self.lookup_path)

        assert len(result['labels']) == 0

    def test_analyze_labels_when_lookup_path_invalid(self):
    
        # Expecting failure when lookup path is invalid
        result,_ = autolabeling.analyze_labels(
            self.gt_path,
            self.file_path,
            self.analyze_result,
            self.key_field_names,
            "test")

        assert len(result['labels']) == 0

    def test_get_key_field_data_when_valid(self):
    
        # Expecting success when all parameters are valid
        result = autolabeling.get_key_field_data(
            self.key_field_names[0],
            self.key_field_details)

        assert result != None

    def test_get_key_field_data_when_details_invalid(self):
    
        # Expecting failure when key fields details are invalid
        result = autolabeling.get_key_field_data(
            self.key_field_names[0],
            "test")

        assert result == None

    def test_get_key_field_data_when_field_name_invalid(self):
    
        # Expecting failure when field name is invalid
        result = autolabeling.get_key_field_data(
            "test",
            self.key_field_details)

        assert result == None

    def test_create_label_file_when_valid(self):
    
        # Expecting success when all parameters are valid
        result,_ = autolabeling.create_label_file(
            self.file_name,
            self.key_field_names,
            self.key_field_details)

        assert result != None

    def test_create_label_file_when_file_name_invalid(self):
    
        # Expecting failure when file name is invalid
        result = autolabeling.create_label_file(
            [],
            self.key_field_names,
            self.key_field_details)

        assert result == None

    def test_create_label_file_when_key_fields_invalid(self):
    
        # Expecting failure when key field names are invalid
        result = autolabeling.create_label_file(
            self.file_name,
            "test",
            self.key_field_details)

        assert len(result['labels']) == 0

    def test_create_label_file_when_details_invalid(self):
    
        # Expecting failure when details are invalid
        result = autolabeling.create_label_file(
            self.file_name,
            self.key_field_names,
            "test")

        assert len(result['labels']) == 0

    def test_build_keys_json_object_when_valid(self):
    
        # Expecting success when all parameters are valid
        result,_ = autolabeling.build_keys_json_object(
            self.keys,
            self.file_name,
            self.key_field_names[0],
            self.found_keys,
            self.ocr_text,
            self.ocr_boundingbox,
            self.page,
            self.height,
            self.width)

        assert len(result[self.file_name]) > 0

    def test_build_keys_json_object_when_keys_invalid(self):
    
        # Expecting failure when keys is invalid
        result,_ = autolabeling.build_keys_json_object(
            None,
            self.file_name,
            self.key_field_names[0],
            self.found_keys,
            self.ocr_text,
            self.ocr_boundingbox,
            self.page,
            self.height,
            self.width)

        assert result == None

    def test_build_keys_json_object_when_filename_invalid(self):
    
        # Expecting failure when filename is invalid
        result,_ = autolabeling.build_keys_json_object(
            self.keys,
            "",
            self.key_field_names[0],
            self.found_keys,
            self.ocr_text,
            self.ocr_boundingbox,
            self.page,
            self.height,
            self.width)

        assert result == None

    def test_build_keys_json_object_when_found_keys_invalid(self):
    
        # Expecting failure when found keys is invalid
        result,_ = autolabeling.build_keys_json_object(
            self.keys,
            self.file_name,
            self.key_field_names[0],
            "",
            self.ocr_text,
            self.ocr_boundingbox,
            self.page,
            self.height,
            self.width)

        assert result == None

    def test_convert_bbox_to_polygon_when_valid(self):
    
        # Expecting success when all parameters are valid
        result = autolabeling.convert_bbox_to_polygon(
                    self.ocr_boundingbox, 
                    self.width, 
                    self.height)

        assert len(result) > 0

    def test_convert_bbox_to_polygon_when_bbox_invalid_empty(self):
    
        # Expecting failure when bbox is invalid (empty array)
        result = autolabeling.convert_bbox_to_polygon(
                    [], 
                    self.width, 
                    self.height)

        assert result == None

    def test_convert_bbox_to_polygon_when_bbox_invalid_incorrect_number_of_values(self):
    
        # Expecting failure when bbox is invalid (incorrect number of values)
        result = autolabeling.convert_bbox_to_polygon(
                    [2,3,4], 
                    self.width, 
                    self.height)

        assert result == None

    def test_convert_bbox_to_polygon_when_width_invalid(self):
    
        # Expecting failure when width is invalid
        result = autolabeling.convert_bbox_to_polygon(
                    self.ocr_boundingbox, 
                    "test", 
                    self.height)

        assert result == None

    def test_convert_bbox_to_polygon_when_height_invalid(self):
    
        # Expecting failure when height is invalid
        result = autolabeling.convert_bbox_to_polygon(
                    self.ocr_boundingbox, 
                    self.width, 
                    "test")

        assert result == None




    
    
        

    
    





   