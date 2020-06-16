#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging
import re
from decimal import Decimal
import moment
import string
import datetime

def normalize(value, method):
    if method == 'date':
        value = date_format(value)
    elif method == 'money':
        value = money_format(value)
    elif method == 'postalCode':
        value = postalcode_format(value)
    elif method == 'address':
        value = address_format(value)
    elif method == 'state':
        value = state_format(value)
    elif method == 'country':
        value = country_format(value)
    else:
        value = text_format(value)
    return value

def format_subfields(text, types):
    if len(types) == 1:
        return normalize(text,types[0])
    sub_text = text.split(" ")
    formatted_text = ""
    word_list = sub_text.copy()
    try:
        # If there is one word per sub field, we apply the corresponding formatting to each word
        if len(sub_text) == len(types):
            for i in range(len(sub_text)):
                word_list[i] = normalize(sub_text[i], types[i])
        # If there are more words than there is subfields, we don't know the type of each word
        else:
            word_list[0] = normalize(sub_text[0], types[0])
            word_list[-1] = normalize(sub_text[-1], types[-1])
            for i in range(1,len(sub_text)-1):
                text_type = guess_type(sub_text[i])
                word_list[i] = normalize(sub_text[i], text_type)
        formatted_text = " ".join(w for w in word_list)
    except Exception as e:
        print(f"Error formatting sub fields: {e}")
    return formatted_text

def remove_trailing_spaces(text):
    # removing spaces at the end and beginning of a string
    try:
        if text != '':
            while(text[-1] == ' '):
                text = text[:-1]
            while(text[0] == ' '):
                text = text[1:]
            # replacing double spaces
            while(text.count('  ') > 0):
                text = text.replace('  ',' ')  
    except Exception:
        pass
    return text


def date_format(value):
    try:
        if("datetime.datetime" in str(value)):
            value = str(value).replace(')','')
            parts = value.split('(')
            date_values = parts[-1].split(',')
            if len(date_values) == 5:
                formated = datetime.datetime(
                    int(date_values[0]), int(date_values[1]), int(date_values[2]), int(date_values[3]), int(date_values[4]))
            else:
                formated = ''
        else:
            try:
                formated = moment.date(value).date
            except Exception:
                # Adding year in case the date only contains day and month
                value = value + '/' + str(datetime.datetime.now().year)
                formated = moment.date()
        formated_str = formated.strftime('%m/%d/%Y')
        value = formated_str
    except Exception:
        try:
            value = str(value)
            # Removing ':', ',', '.' in case there was noise on the invoice
            value = value.replace(':','')
            value = value.replace(',','')
            value = value.replace('.','')
            value = value.replace(' ', '')
            formated = moment.date(value).date
            formated_str = formated.strftime('%m/%d/%Y')
            value = formated_str
        except Exception:
            pass
    return value

def money_format(value):
    try:
        value = str(value)
        # If the amount is in the format 59.68 and not 1,273.98
        if(value.count('.') == 0 and len(value.split(',')[1]) <= 2):
            value = value.replace(',','.')
        value = str(Decimal(re.sub(r'[^\d.]', '', str(value))))
        if(len(value.split('.')[-1]) == 1):
            value += '0'
    except Exception:
        pass
    return str(value)

def postalcode_format(value):
    try:
        value = str(value).split('-')[0]
    except Exception:
        pass
    # In the GT, when there are 0s at the beginning of the PC they are deleted by Excel so we add them back
    if len(value) < 5:
        zeros = '0'*(5-len(value))
        value = zeros + str(value)
    return value

def state_format(value):
    # Removing all punctuation
    value = value.translate(str.maketrans(string.punctuation,' ' * len(string.punctuation)))
    value = str(value).replace(' ', '')
    return value

def text_format(value):
    try:
        value = re.sub(r'\s+', ' ', value.encode('ascii', 'ignore')
                            .decode('ascii')
                            .strip()
                            .lower()
                            .translate(str.maketrans(string.punctuation,
                                                     ' ' * len(string.punctuation))))
        value = value.replace(' ','')
    except Exception:
        pass
    return str(value)

def address_format(value):

    # Removing all punctuation
    value = value.translate(str.maketrans(string.punctuation,' ' * len(string.punctuation)))
    
    # Separating address in several parts
    address_parts = value.split(' ')
    formatted_parts = ["","",""]
    formatted_address = ""
    road_name = ""

    directions = ["n", "s", "w", "e"]
    abbrev = ["ste"]

    directions_mapping = {
        "n": "north",
        "s": "south",
        "w": "west",
        "e": "east"
    }

    abbrev_mapping = {
        "ste": "suite"
    }
    
    skip_words = ['ofc', 'apt', 'llc']

    for part in address_parts:

        # If it's the number, we keep it as is and put it in first position
        if part.isnumeric():
            formatted_parts[0] += part
        # If it's the road type, we format it and put it in third position
        elif isroadtype(part):
            formatted_parts[2] = road_format(part)
        # If there's a direction, we replace it by the whole direction name
        elif part.lower() in directions:
            part = directions_mapping[part.lower()]
            road_name += part
        # If there's an abbreviation, we replace it by the whole word
        elif part.lower() in abbrev:
            part = abbrev_mapping[part.lower()]
            road_name += part
        # If there's an information that's not part of the standardized address, we skip it
        elif part.lower() in skip_words:
            part = ''
        # If it's the road name, we format it and put it in second position
        else:
            road_name += part

    formatted_parts[1] = text_format(road_name)
    formatted_address = ' '.join(p for p in formatted_parts)

    return formatted_address


def isroadtype(text):
    main_roadtypes = ["road", "street", "highway", "way", "avenue", "alley", "boulevard", "lane", "route", "terrace", "court", "drive", "parkway", "circle"]
    abbrev_roadtypes = ["rd", "st", "hwy", "av", "blvd", "bd", "bvd", "ln", "aly", "ave", "dr", "pkwy", "cir"]
    try:
        if(text.lower() in main_roadtypes or text.lower() in abbrev_roadtypes):
            return True
    except Exception:
        pass
    return False

def road_format(text):
    main_roadtypes = ["road", "street", "highway", "way", "avenue", "alley", "boulevard", "lane", "route", "terrace", "court", "drive", "parkway", "circle"]
    map_abbrev = {
        "rd": "road",
        "st": "street", 
        "hwy": "highway", 
        "av":"avenue", 
        "blvd": "boulevard", 
        "bd": "boulevard", 
        "bvd": "boulevard", 
        "ln": "lane", 
        "aly": "alley", 
        "ave": "avenue", 
        "dr": "drive",
        "pkwy": "parkway",
        "cir": "circle"
    }

    text = text.lower()
    if(text in main_roadtypes):
        return text
    else:
        try:
            text = map_abbrev[text]
        except Exception:
            pass
    return text

def country_format(text):
    mapping_countries = {
        "fr": "france",
        "us": "united states",
        "usa": "united states",
        "uk": "united kingdom",
        "gb": "great britain"
    }

    text = text.lower()
    try: 
        text = mapping_countries[text]
    except Exception:
        pass

    return text

def guess_type(text):
    if is_date(text):
        return "date"
    elif is_state(text):
        return "state"
    elif is_postalcode(text):
        return "postalCode"
    else:
        return "text"


def find_subtext(text, field_type):

    months_en = ['jan', 'feb', 'febr', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'sept', 'oct', 'nov', 'dec',
                'january', 'february', 'march', 'april', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
    months_fr = ['jan', 'fev', 'mar', 'avr', 'mai', 'juin', 'juil', 'aout', 'sep', 'sept', 'oct', 'nov', 'dec',
                'janvier', 'fevrier', 'février', 'mars', 'avril', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'decembre', 'décembre']

    date_num1 = r'\d{1,2}\/\d{1,2}\/\d{2,4}'
    date_num2 = r'\d{1,2}\/\d{1,2}'
    date_alpha_en1 = r'(?:%s)\s+\d{1,2}\s*\d{2,4}' % '|'.join(months_en)
    date_alpha_en2 = r'%s\s+\d{1,2}' % '|'.join(months_en)
    date_alpha_fr1 = r'\d{1,2}\s+(?:%s)\s*\d{2,4}' % '|'.join(months_fr)
    date_alpha_fr2 = r'\d{1,2}\s+(?:%s)' % '|'.join(months_fr)

    date_regex = [re.compile(date_num1), 
                    re.compile(date_num2),
                    re.compile(date_alpha_en1),
                    re.compile(date_alpha_fr1),
                    re.compile(date_alpha_en2),
                    re.compile(date_alpha_fr2)]

    try:

        if field_type != "":
            text_parts = text.split(' ')

            # Finding sub text of type state
            if field_type == 'state':
                for part in text_parts:
                    if is_state(part):
                        return part

            # Finding sub text of type postal code
            elif field_type == 'postalCode':
                for part in text_parts:
                    if is_postalcode(part):
                        return part

            # Finding sub text of type city
            elif field_type == 'city':
                city = ""
                for part in text_parts:
                    if not(is_state(part)) and not(is_postalcode(part)):
                        city = city + part + " "
                # Removing whitespace at the end
                if(city[-1] == " "):
                    city = city[:-1]
                return city

            # Finding sub text of type date
            elif field_type == 'date':
                text = text.replace('.','')     
                for regex in date_regex:
                    reg_date = regex.findall(text)
                    if len(reg_date) > 0:
                        return reg_date[0]

    except Exception:
        pass
    
    return text

def is_date(text):
    try:
        if len(text) <= 10 and len(text) >= 6 and text.count('/') == 2:
            return True
        split_date = text.lower().split(" ")
        months = ["january", "february", "march", "april", "may", "june", "july", "september", "october", "november", "december",
                    "jan", "feb", "febr", "mar", "apr", "jun", "jul", "sep", "sept", "oct", "nov", "dec"]
        if len(split_date) == 3:
            for i in split_date:
                if i in months:
                    return True
    except Exception:
        pass
    return False

def is_state(text):
    states = []
    try:
        if text.isupper() and len(text) == 2:
            # TODO: Add a list of states
            #if text in states:
            return True
    except Exception:
        pass
    return False

def is_postalcode(text):
    try:
        if text.isnumeric() and len(text) == 5:
            return True
        postalparts = text.split('-')
        if len(postalparts) == 2 and postalparts[0].isnumeric() and len(postalparts[0]) == 5:
            return True
    except Exception:
        pass
    return False
    