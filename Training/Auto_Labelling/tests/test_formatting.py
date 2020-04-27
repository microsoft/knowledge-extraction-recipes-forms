import pytest
import unittest
import os
import json
from mock import MagicMock, patch, mock_open

from shared_code import formatting

@pytest.mark.formatting
class NormalizeTest(unittest.TestCase):

    text_value = "Hello, world!"
    text_normalized = "helloworld"

    date_value = "2/8/20"
    date_normalized = "02/08/2020"
    date_wrong = "2820"

    money_value = "$3,214"
    money_normalized = "3214"

    postalcode_value = "43517-4554"
    postalcode_normalized = "43517"

    state_value = "MI,"
    state_normalized = "MI"

    address_value = "4200 Hollywood Blvd"
    address_normalized = "4805 hollywood boulevard" 

    road_value = "ST"
    road_normalized = "street"

    def test_normalize_date(self):

        # Expecting date to be correctly formatted when the right method is provided
        result = formatting.normalize(
                self.date_value,
                "date")

        assert result == self.date_normalized

    def test_normalize_date_when_wrong_method(self):

        # Expecting date to be wrongly formatted when the wrong method is provided
        result = formatting.normalize(
                self.date_value,
                "text")

        assert result == self.date_wrong

    def test_normalize_text(self):

        # Expecting formatted text
        result = formatting.normalize(
                self.text_value,
                "text")

        assert result == self.text_normalized

    def test_normalize_else(self):

        # Expecting formatted text as default is text
        result = formatting.normalize(
                self.text_value,
                "")

        assert result == self.text_normalized

    def test_date_format(self):

        # Expecting date formatting
        result = formatting.date_format(
                self.date_value)

        assert result == self.date_normalized

    def test_money_format(self):

        # Expecting money formatting
        result = formatting.money_format(
                self.money_value)

        assert result == self.money_normalized

    def test_postalcode_format(self):

        # Expecting postalcode formatting
        result = formatting.postalcode_format(
                self.postalcode_value)

        assert result == self.postalcode_normalized

    def test_state_format(self):

        # Expecting state formatting
        result = formatting.state_format(
                self.state_value)

        assert result == self.state_normalized
    
    def test_text_format(self):

        # Expecting text formatting
        result = formatting.text_format(
                self.text_value)

        assert result == self.text_normalized

    def test_address_format(self):

        # Expecting address formatting
        result = formatting.address_format(
                self.address_value)

        assert result == self.address_normalized

    def test_road_format(self):

        # Expecting road formatting
        result = formatting.road_format(
                self.road_value)

        assert result == self.road_normalized

    def test_remove_trailing_spaces(self):

        value_trailing_spaces = "  Hello   there,     how are    you?     "
        value_normalized = "Hello there, how are you?"

        # Expecting value to be normalized
        result = formatting.remove_trailing_spaces(
            value_trailing_spaces)
        
        assert result == value_normalized



@pytest.mark.formatting
class FormatSubfieldsTest(unittest.TestCase):

    value1 = "Salt Lake City UT 84044-1234"
    text_normalized = "saltlakecityut840441234"
    value2 = "Seattle WA 98101"
    types = ["city", "state", "postalCode"]
    address_normalized1 = "salt lake city UT 84044"
    address_normalized2 = "seattle WA 98101"
    

    def test_format_subfields_when_one_type(self):

        # Expecting formatting to succeed when there's only one type
        result = formatting.format_subfields(
                self.value1,
                ["text"])

        assert result == self.text_normalized

    def test_format_subfields_when_several_types_and_same_word_number(self):

        # Expecting formatting to succeed when there are several types and one word per type
        result = formatting.format_subfields(
                self.value2,
                self.types)

        assert result == self.address_normalized2

    def test_format_subfields_when_several_types_and_different_word_number(self):

        # Expecting formatting to succeed when there are several types and not the same number of words
        result = formatting.format_subfields(
                self.value1,
                self.types)

        assert result == self.address_normalized1

    def test_format_subfields_when_wrong_types_and_different_word_number(self):

        # Expecting formatting to fail when there are wrong types and not the same number of words
        result = formatting.format_subfields(
                self.value1,
                ["state", "postalCode", "city"])

        assert result != self.address_normalized1

    def test_format_subfields_when_one_type_and_different_word_number(self):

        # Expecting formatting to fail when there's only one type and not the same number of words
        result = formatting.format_subfields(
                self.value1,
                ["text"])

        assert result != self.address_normalized1


    def test_format_subfields_when_type_empty_array(self):

        # Expecting empty string when an empty array is provided
        result = formatting.format_subfields(
                self.value1,
                [])

        assert result == ""

    def test_format_subfields_when_type_is_string(self):

        # Expecting formatting to fail when a string is provided
        result = formatting.format_subfields(
                self.value1,
                "test")

        assert result != self.address_normalized1


@pytest.mark.formatting
class FindTypeTest(unittest.TestCase):

    road_value = "RD"
    date_value = "7/8/19"
    postalcode_value = "12345-6789"
    state_value = "MI"
    test_value = "test"
    invalid_value = []

    address_value = "Salt Lake City UT 84044-1234"
    city_subtext = "Salt Lake City"
    state_subtext = "UT"
    postalcode_subtext = "84044-1234"

    def test_is_road_when_road(self):

        # Expecting True when value is road
        result = formatting.isroadtype(
                self.road_value)

        assert result == True

    def test_is_road_when_not_road(self):

        # Expecting False when value is not road
        result = formatting.isroadtype(
                self.test_value)

        assert result == False

    def test_is_road_when_invalid(self):

        # Expecting False when value is invalid
        result = formatting.isroadtype(
                self.invalid_value)

        assert result == False

    def test_is_date_when_date(self):

        # Expecting True when value is date
        result = formatting.is_date(
                self.date_value)

        assert result == True

    def test_is_date_when_not_date(self):

        # Expecting False when value is not date
        result = formatting.is_date(
                self.test_value)

        assert result == False

    def test_is_date_when_invalid(self):

        # Expecting False when value is invalid
        result = formatting.is_date(
                self.invalid_value)

        assert result == False

    def test_is_postalcode_when_postalcode(self):

        # Expecting True when value is postalcode
        result = formatting.is_postalcode(
                self.postalcode_value)

        assert result == True

    def test_is_postalcode_when_not_postalcode(self):

        # Expecting False when value is not postalcode
        result = formatting.is_postalcode(
                self.test_value)

        assert result == False

    def test_is_postalcode_when_invalid(self):

        # Expecting False when value is invalid
        result = formatting.is_postalcode(
                self.invalid_value)

        assert result == False

    def test_is_state_when_state(self):

        # Expecting True when value is state
        result = formatting.is_state(
                self.state_value)

        assert result == True

    def test_is_state_when_not_state(self):

        # Expecting False when value is not state
        result = formatting.is_state(
                self.test_value)

        assert result == False

    def test_is_state_when_invalid(self):

        # Expecting False when value is invalid
        result = formatting.is_state(
                self.invalid_value)

        assert result == False

    def test_find_subtext_when_state(self):

        # Expecting state to be found
        result = formatting.find_subtext(
                self.address_value,
                "state")

        assert result == self.state_subtext

    def test_find_subtext_when_city(self):

        # Expecting city to be found
        result = formatting.find_subtext(
                self.address_value,
                "city")

        assert result == self.city_subtext

    def test_find_subtext_when_postalcode(self):

        # Expecting postalcode to be found
        result = formatting.find_subtext(
                self.address_value,
                "postalCode")

        assert result == self.postalcode_subtext

    def test_find_subtext_when_state_not_here(self):

        # Expecting state not to be found
        result = formatting.find_subtext(
                self.test_value,
                "state")

        assert result != self.state_subtext

    def test_find_subtext_when_postalcode_not_here(self):

        # Expecting postalcode not to be found
        result = formatting.find_subtext(
                self.test_value,
                "postalCode")

        assert result != self.postalcode_subtext

    def test_guess_type_when_date(self):

        # Expecting type to be date
        result = formatting.guess_type(
                self.date_value)

        assert result == "date"
    
    def test_guess_type_when_state(self):

        # Expecting type to be state
        result = formatting.guess_type(
                self.state_value)

        assert result == "state"

    def test_guess_type_when_postalcode(self):

        # Expecting type to be postalCode
        result = formatting.guess_type(
                self.postalcode_value)

        assert result == "postalCode"

    def test_guess_type_when_text(self):

        # Expecting type to be text
        result = formatting.guess_type(
                self.test_value)

        assert result == "text"

    


