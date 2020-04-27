import logging
import datetime
import re
import moment       # type:ignore
import pandas as pd     # type:ignore
import string
import requests 
import json

def is_valid(value):
    if value == '' or value == 'NULL' or value == 'nan' or value == None or value == 'none':
        return False
    return True

def load_excel(file_path):
    try:
        df = pd.read_excel(file_path)
        print(f"Information from excel file {file_path} successfully retrieved.")
        return df
    except Exception as e:
        print(f"Could not get information from excel file {file_path}: {e}")
        return pd.DataFrame()

def get_model_details(train_response, training_type):
    model_details = None
    try:
        model_details = {}
        model_details['model_id'] = train_response['modelInfo']['modelId']
        model_details['status'] = train_response['modelInfo']['status']
        model_details['date'] = train_response['modelInfo']['createdDateTime']
        if training_type == 'supervised':
            model_details['accuracy'] = train_response['trainResult']['averageModelAccuracy']
            model_details['fields_accuracy'] = train_response['trainResult']['fields']
        else:
            model_details['accuracy'] = ""
            model_details['fields_accuracy'] = ""
        logging.info(f"Retrieved model details. Model ID: {model_details['model_id']}")
    except Exception as e:
        logging.error(f"Could not get model details: {e}")
    return model_details

def create_results_files(model_details, doctype):

    autolabel_results = "\n" + doctype + "," + model_details['model_id'] + "," + \
                        model_details['status'] + "," + str(model_details['accuracy'])
    data = {'doctype': [doctype], 'modelId': [model_details['model_id']],
            'status': [model_details['status']], 'accuracy': [model_details['accuracy']],
            'fieldsAccuracy': [str(model_details['fields_accuracy'])]}
    df_lookup = pd.DataFrame(data)
    csv_output = df_lookup.to_csv(sep=';')

    return autolabel_results, csv_output

def is_number(input):
    return isinstance(input, (int, float, complex)) and not isinstance(input, bool)

def is_url(input):
    if input is None:
        raise ValueError("is_url input is None!")
    elif input == "":
        raise ValueError("is_url input is empty string!")
    elif is_number(input):
        raise ValueError("is_url input is numeric! Must be string")
    elif not isinstance(input, str):
        raise ValueError("is_url input must be string")

    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)  
    return re.match(regex, input) != None

def get_lookup_fields_from_url(lookup_path):
    logging.info(f"Loading lookup file from url. Url: {lookup_path}")
    r = requests.get(url = lookup_path) 
    return r.json()     

def get_lookup_fields_from_file(lookup_path):
    logging.info(f"Loading lookup file from disk. Path: {lookup_path}")
    with open(lookup_path) as f:
        return json.load(f)    

def get_lookup_fields(lookup_path):
    lookup_fields = None
    try:
        lookup_fields = get_lookup_fields_from_url(lookup_path) if is_url(lookup_path) else get_lookup_fields_from_file(lookup_path)
    except Exception as e:
        logging.error(f"Error loading lookup file: {e}")
    return lookup_fields
