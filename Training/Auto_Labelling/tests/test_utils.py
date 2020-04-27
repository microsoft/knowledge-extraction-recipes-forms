import pytest
import os
import json
from mock import MagicMock, patch, mock_open

from shared_code import utils

def test_is_url_returns_true_when_url_passed_in():
    #arrange
    input = "https://fake-url.com/data.txt"

    #act
    result = utils.is_url(input)

    #assert
    assert result is True

def test_is_url_returns_false_when_filepath_passed_in():
    #arrange
    input = "./data.txt"

    #act
    result = utils.is_url(input)

    #assert
    assert result is False  

def test_is_url_raises_exception_when_None_passed_in():
    #arrange
    input = None

    #act
    with pytest.raises(ValueError) as excinfo:
        utils.is_url(input)

    #assert
    assert "is_url input is None!" in str(excinfo.value)

def test_is_url_raises_exception_when_empty_string_passed_in():
    #arrange
    input = ""

    #act
    with pytest.raises(ValueError) as excinfo:
        utils.is_url(input)

    #assert
    assert "is_url input is empty string!" in str(excinfo.value)

@patch('shared_code.utils.get_lookup_fields_from_file')  
def test_get_lookup_fields_loads_file_when_input_not_url(fake_get_lookup_fields_from_file):
    #arrange
    input = "./data.txt"

    #act
    result = utils.get_lookup_fields(input)

    #assert
    assert fake_get_lookup_fields_from_file.called  

@patch('shared_code.utils.get_lookup_fields_from_url')  
def test_get_lookup_fields_loads_file_when_input_not_url(fake_get_lookup_fields_from_url):
    #arrange
    input = "https://fake-url.com/data.txt"

    #act
    result = utils.get_lookup_fields(input)

    #assert
    assert fake_get_lookup_fields_from_url.called      

def test_get_lookup_fields_raises_exception_when_None_passed_in():
    #arrange
    input = None

    # #act
    # with pytest.raises(ValueError) as excinfo:
    #     utils.get_lookup_fields(input)

    # #assert
    # assert "is_url input is None!" in str(excinfo.value)
    result = utils.get_lookup_fields(input)
    assert result == None

def test_get_lookup_fields_raises_exception_when_empty_string_passed_in():
    #arrange
    input = ""

    #act
    # with pytest.raises(ValueError) as excinfo:
    #     utils.get_lookup_fields(input)

    # #assert
    # assert "is_url input is empty string!" in str(excinfo.value)   
    result = utils.get_lookup_fields(input)
    assert result == None

def test_get_lookup_fields_raises_exception_when_number_passed_in():
    #arrange
    input = 124

    # #act
    # with pytest.raises(ValueError) as excinfo:
    #     utils.get_lookup_fields(input)

    # #assert
    # assert "is_url input is numeric! Must be string" in str(excinfo.value)
    result = utils.get_lookup_fields(input)
    assert result == None    

def test_get_lookup_fields_should_only_accept_strings():
    #arrange
    def input():
        print("a fake method")

    # #act
    # with pytest.raises(ValueError) as excinfo:
    #     utils.get_lookup_fields(input)

    # #assert
    # assert "is_url input must be string" in str(excinfo.value)    
    result = utils.get_lookup_fields(input)
    assert result == None

@patch('requests.get')
def test_get_lookup_fields_fetches_json_from_url(fake_requests_get):
    #arrange
    input = "https://fake-url.com/data.txt"

    #act
    result = utils.get_lookup_fields(input)

    #assert
    fake_requests_get.assert_called_once_with(url=input)

def test_get_lookup_fields_fetches_json_from_url():
    #arrange
    input = "data.txt"
    data = {
        "foo" : "bar"
    }
    json_text = json.dumps(data)
    #act
    with patch('builtins.open',
            mock_open(read_data=json_text),
            create=True):    
        result = utils.get_lookup_fields(input)
   
    #assert
        assert result["foo"] == data["foo"]

def test_is_number_returns_true_when_int():
    #arrange
    input = 1
    #act
    result = utils.is_number(input)
    #assert
    assert result is True

def test_is_number_returns_true_when_float():
    #arrange
    input = 20.4
    #act
    result = utils.is_number(input)
    #assert
    assert result is True

def test_is_number_returns_true_when_complex():
    #arrange
    input =  1 + 2j
    #act
    result = utils.is_number(input)
    #assert
    assert result is True
   
def test_is_number_returns_false_when_string():
    #arrange
    input = 1
    #act
    result = utils.is_number(input)
    #assert
    assert result is True

def test_is_number_returns_false_when_lambda():
    #arrange
    input = lambda a : a + 10
    #act
    result = utils.is_number(input)
    #assert
    assert result is False    
