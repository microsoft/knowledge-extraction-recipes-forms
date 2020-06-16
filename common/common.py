#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import datetime
import os
import re
import string
import sys
import cv2
from PIL import Image
import numpy as np

import moment  # type:ignore
import pandas as pd  # type:ignore
from fuzzywuzzy import fuzz, process  # type:ignore


def sum_bounding_box(bbox):
    """

    :param bbox: Bounding box of the associated text
    :return: A single int
    """
    return sum(bbox)


def extract_ocr_as_textblock(df_ocr):
    """

    :param df_ocr: Dataframe of the OCR of a single invoice
    :return: A text block that is lower case, stripped of leading, training whitespaces and punctuation
    """

    raw_text = ''

    for _, row_inv in enumerate(df_ocr.itertuples(), 1):
        raw_text += row_inv.data_word.encode('ascii', 'ignore').decode('ascii') + ' '

    raw_text = strip_lower_remove_punctuation(raw_text)

    return raw_text


def get_text_from_ocr(res):
    """
    Simply extract the text from OCR
    :param res: OCR result string
    :return: The text only
    """
    res_string = ''
    for pages in res['analyzeResult']['readResults']:  # Added page
        for lines in pages['lines']:
            for words in lines['words']:
                res_string += words['text']

    return res_string


def strip_lower_remove_punctuation(input_string):
    """

    :param input_string: Input string as is
    :return: string without leading, trailing or double+ white spaces, lower case and no punctuation, ascii characters
    only
    """

    cleaned_string = ''
    cleaned_string = re.sub(r'\s+', ' ', input_string.encode('ascii', 'ignore')
                            .decode('ascii')
                            .strip()
                            .lower()
                            .translate(str.maketrans(string.punctuation,
                                                     ' ' * len(string.punctuation))))
    return cleaned_string


def extract_ocr_as_textblock_with_punct(df_ocr):
    """

    :param df_ocr: Dataframe of the OCR of a single invoice
    :return: A text block that is lower case, stripped of leading, training whitespaces and punctuation
    """

    raw_text = ''

    for _, row_inv in enumerate(df_ocr.itertuples(), 1):
        raw_text += row_inv.data_word.encode('ascii', 'ignore').decode('ascii') + ' '

    raw_text = raw_text.strip().lower()

    return raw_text


def find_issuer_in_invoice_text(dfissuers, raw_text, filename, search_term_issuer_found):
    """

    :param dfissuers: The issuer lookup file as a dataframe
    :param raw_text: The OCR text
    :param filename: The full name of the invoice file processed
    :param search_term_issuer_found: A counter for found records
    :return: Equal length lists that will be used to construct the vendor cluster dataframe
    """

    lst_files = []
    lst_issuernames = []
    lst_issuernumbers = []
    lst_issuerzips = []
    lst_ibans = []
    lst_vat = []
    lst_score = []

    # Clean raw text from OCR
    raw_text = strip_lower_remove_punctuation(raw_text)
    # Get digit only text for fuzzy matching of IBAN and VAT
    digit_block_text = re.sub("[^0-9]", "", raw_text)

    for _, row_ven in dfissuers.iterrows():

        # We are going to score the issuers on various fields
        # TODO Add your issuer name here
        issuername = strip_lower_remove_punctuation(row_ven['Your Issuer Name'])

        # TODO Add your post code here
        zipcode = strip_lower_remove_punctuation(row_ven['Your Post Code'])

        # TODO Add your Iban/Bank Account here
        iban = str(row_ven['Your Bank number']).strip()

        # TODO Add your issuer unique number here
        issuernumber = str(row_ven['Your Issuer number here']).strip()

        # TODO Add your VAT number here
        vat = strip_lower_remove_punctuation(str(row_ven['Your VAT Number']))

        # Reset score
        total = 0
        score = 0
        pscore = 0
        found_issuer = False
        found_zip = False
        found_vat = False
        found_iban = False
        candidate_search = ''

        # Straight regex first
        # TODO add your own data specific formatting
        found_issuer = is_phrase_in(issuername, raw_text)
        if len(zipcode) > 0:
            found_zip = is_phrase_in(zipcode, raw_text.lower())
        if len(iban) > 0:
            found_iban = is_phrase_in(iban, raw_text.lower())
        if len(vat) > 0:
            found_vat = is_phrase_in(vat, raw_text.lower())

        if found_zip:
            total += 100  # TODO add your own weighting here
        else:
            # Let's check for parts of the zipcode in case of an OCR error
            if zipcode.find(' '):
                pos = zipcode.find(' ')
                found_zip = is_phrase_in(zipcode[:pos], raw_text.lower())
                # Build composite of the postal in the event of OCR errors
                if found_zip:
                    pos = raw_text.lower().find(zipcode[:pos])
                    ocr_error_zip = raw_text[pos:len(zipcode) + pos].lower()
                    score = compute_ratio(ocr_error_zip, zipcode)
                    pscore = compute_partial_ratio(ocr_error_zip, zipcode)
                    total += score
                    total += pscore
                else:  # Check second part
                    found_zip = is_phrase_in(zipcode[pos:], raw_text.lower())
                    if found_zip:
                        zip_second_part = len(zipcode[pos:])
                        pos = raw_text.lower().find(zipcode[pos:])
                        ocr_error_zip = raw_text[pos - (len(zipcode) - zip_second_part):pos].lower()
                        score = compute_ratio(ocr_error_zip, zipcode)
                        pscore = compute_partial_ratio(ocr_error_zip, zipcode)
                        total += score
                        total += pscore

        if found_iban:
            total += 100  # TODO add your own weighting here
        else:
            if (len(iban) > 0) and (iban is not None) and (iban != 'nan'):
                # To decide - skip iban_patterns and go directly to fuzzy_digit_matching
                # Let's apply a common mask
                lst_iban_masks = iban_patterns(iban, len(iban))
                for iban in lst_iban_masks:
                    found_iban = is_phrase_in(iban, raw_text.lower())
                    if found_iban:
                        total += 100  # TODO add your own weighting here
                        break
                if not found_iban:
                    found_iban = fuzzy_digit_matching(iban, digit_block_text)
                    if found_iban:
                        total += 100  # TODO add your own weighting here

        if found_vat:
            total += 100  # TODO add your own weighting here

        else:
            if (len(vat) > 0) and (vat is not None) and (vat != 'nan'):
                # To decide - skip vat_patterns and go directly to fuzzy_digit_matching
                # Let's apply a common mask
                lst_vat_masks = vat_patterns(vat, len(vat))
                for vat in lst_vat_masks:
                    found_vat = is_phrase_in(vat, raw_text.lower())
                    if found_vat:
                        total += 100  # TODO add your own weighting here
                        break
                if not found_vat:
                    found_vat = fuzzy_digit_matching(vat, digit_block_text)
                    if found_vat:
                        total += 100  # TODO add your own weighting here

        # Now we search for issuer name
        if found_issuer:
            total += 100  # TODO add your own weighting here
            search_term_issuer_found += 1
            lst_issuernames.append(issuername)
            lst_issuerzips.append(zipcode)
            lst_ibans.append(iban)
            lst_files.append(str(filename))
            lst_score.append(total)
            lst_issuernumbers.append(issuernumber)
            lst_vat.append(vat)
        else:
            # Let's try to partially match on the vendor name
            lst_issuername = issuername.split()

            if len(lst_issuername) > 0:
                found_issuer = is_phrase_in(lst_issuername[0].lower(), raw_text.lower())

                # Slide through the window
                for i in range(len(lst_issuername)):
                    if i + 2 < len(lst_issuername):
                        candidate_search = lst_issuername[i].lower() + ' ' \
                                           + lst_issuername[i + 1].lower() + ' ' \
                                           + lst_issuername[i + 2].lower()
                        found_issuer = is_phrase_in(candidate_search, raw_text.lower())

                        # Now we try cater for OCR errors
                        if not found_issuer:
                            candidate_search = candidate_search.replace(' ', '')
                            found_issuer = is_phrase_in(candidate_search, raw_text.lower())

                        if found_issuer:
                            break

                    elif i + 1 < len(lst_issuername):
                        candidate_search = lst_issuername[i].lower() + ' ' \
                                           + lst_issuername[i + 1].lower() + ' '
                        found_issuer = is_phrase_in(candidate_search, raw_text.lower())

                        # Now we try cater for OCR errors
                        if not found_issuer:
                            candidate_search = candidate_search.replace(' ', '')
                            found_issuer = is_phrase_in(candidate_search, raw_text.lower())

                        if found_issuer:
                            break

                if found_issuer or found_zip or found_vat or found_iban:

                    vendor_part_sum = 0
                    for vendor_part in lst_issuername:
                        vendor_part_sum += len(vendor_part) + 1

                    pos = raw_text.lower().find(lst_issuername[0].lower())
                    candidate_text = raw_text[pos:pos + vendor_part_sum].lower()
                    score = compute_ratio(candidate_text.lower(), issuername.lower())
                    pscore = compute_partial_ratio(candidate_text.lower(), issuername.lower())

                    # Add mean of ratio scores to total score
                    total += ((score + pscore) / 2)  # TODO apply any custom weighting here

                    lst_issuernames.append(issuername)
                    lst_issuerzips.append(zipcode)
                    lst_files.append(str(filename))
                    lst_ibans.append(iban)
                    lst_score.append(total)
                    lst_vat.append(vat)
                    lst_issuernumbers.append(issuernumber)
                    search_term_issuer_found += 1

    return lst_files, lst_issuernames, lst_issuerzips, lst_ibans, \
           lst_score, lst_issuernumbers, lst_vat, search_term_issuer_found


def find_anchor_key_in_form_text(df_single_form_gt, df_ocr, row, anchor_keys):
    """

    :param df_single_form_gt: The Ground Truth file
    :param df_ocr: A dataframe containing the OCR scan of the form
    :param row: Active dataframe current row from outside loop
    :param anchor_keys: The fields that need to be extracted
    :return: Equal length lists that will be used to construct the cluster dataframe
    """

    # TODO - the lists below will contain the bounding box and other coordinates to return
    lst_files = []
    lst_formnames = []
    lst_bbox_area = []
    lst_bbox_par = []
    lst_bbox_line = []
    lst_bbox_page = []
    lst_anchor_key = []
    lst_page = []

    for anchor_key in anchor_keys:

        for row_ocr in enumerate(df_ocr.itertuples(), 1):
            if len(df_single_form_gt[anchor_key]) == 0:
                continue

            ocr_clean = strip_lower_remove_punctuation(
                row_ocr[1].data_word)
            gt_clean = strip_lower_remove_punctuation(
                str(df_single_form_gt[anchor_key].iloc[0]))

            if ocr_clean == gt_clean:
                lst_formnames.append('Your form name/vendor/author')  # Todo - add your key
                lst_files.append(row['Your file name'])  # TODO - add your filename
                lst_page.append(row_ocr[1].page)
                lst_bbox_area.append(sum_bounding_box(row_ocr[1].bbox_area))
                lst_bbox_page.append(sum_bounding_box(row_ocr[1].bbox_page))
                lst_bbox_par.append(sum_bounding_box(row_ocr[1].bbox_par))
                lst_bbox_line.append(sum_bounding_box(row_ocr[1].bbox_line))
                lst_anchor_key.append(anchor_key)
                break

    data = {'formkey': lst_formnames, 'file': lst_files, 'key': lst_anchor_key, 'page': lst_page,
            'bbox_area': lst_bbox_area, 'bbox_para': lst_bbox_par, 'bbox_line': lst_bbox_line,
            'bbox_page': lst_bbox_page}

    return data


def build_deviations_file(dfukclusterdev, threshold, anchor_key):
    """

    :param dfukclusterdev: The bounding box cluster dataframe
    :param threshold: The threshold above which the standard deviation for a vendor indicates a potential form change
    :param anchor_key: The key field that we are searching for
    :return: A dataframe that contains the standard deviation by vendor
    """

    dfclusterdevinv = dfukclusterdev[dfukclusterdev['key'] == anchor_key]

    dftop3dev = dfclusterdevinv.sort_values(by=['bbox_line_std'], ascending=False)
    dftop3dev = dftop3dev.groupby('bbox_line_std').head(5).reset_index(drop=True)
    # Determine the top 5 values and inspect
    print('The following vendors need to be checked for deviations on', anchor_key, dftop3dev['vendor'].iloc[0],
          dftop3dev['vendor'].iloc[1], dftop3dev['vendor'].iloc[2], dftop3dev['vendor'].iloc[3],
          dftop3dev['vendor'].iloc[4], dftop3dev['vendor'].iloc[5])

    # Get all deviations over threshold
    dfdev = dfclusterdevinv[
        (dfclusterdevinv['bbox_line_std'] > float(threshold)) & (dfclusterdevinv['key'] == anchor_key)]

    return dfdev


def build_max_differences_file(dfclusterbbox, anchor_keys):
    """

    :param dfclusterbbox: The bounding box cluster dataframe
    :param anchor_keys: The key fields we want to find on each invoice
    :return: A dataframe containing the maximum bbox values for each vendor
    """

    box = 'bbox_line'

    # TODO ensure this reflects your key here e.g. issuer
    issuers = list(set(list(dfclusterbbox['issuer'].unique())))
    lst_issuers = []
    lst_keys = []
    lst_bbox_maxs = []
    lst_bbox_maxs_files = []
    lst_bbox_mins = []
    lst_bbox_mins_files = []
    lst_bbox_diff = []

    # TODO add your keys here
    for issuer in issuers:
        # TODO ensure this reflects your key here e.g. issuer
        dfissuer = dfclusterbbox[dfclusterbbox['issuer'] == issuer].dropna()
        for anchor_key in anchor_keys:
            if anchor_key in list(dfissuer['key']):
                lst_issuers.append(issuer)
                lst_keys.append(anchor_key)
                dfissuer_key = dfissuer[dfissuer['key'] == anchor_key]
                bbox_max_index = dfissuer_key[box].idxmax()
                lst_bbox_maxs.append(dfissuer_key.loc[bbox_max_index][box])
                lst_bbox_maxs_files.append(dfissuer_key.loc[bbox_max_index]['file'])
                bbox_min_index = dfissuer_key[box].idxmin()
                lst_bbox_mins.append(dfissuer_key.loc[bbox_min_index][box])
                lst_bbox_mins_files.append(dfissuer_key.loc[bbox_min_index]['file'])
                lst_bbox_diff.append(int(lst_bbox_maxs[-1]) - int(lst_bbox_mins[-1]))

    dfukcluster_maxmin = pd.DataFrame({'issuer': lst_issuers,
                                       'key': lst_keys,
                                       'bbox_max': lst_bbox_maxs,
                                       'bbox_max_file': lst_bbox_maxs_files,
                                       'bbox_min': lst_bbox_mins,
                                       'bbox_min_file': lst_bbox_mins_files,
                                       'bbox_diff': lst_bbox_diff})

    return dfukcluster_maxmin


def build_keys_json_object(keys, blobname, anchor_key, found_keys, ocr_text, ocr_boundingbox,
                           page, height, width):
    """
    This function build the json object for the auto-labelling
    :param keys: The json object
    :param blobname: The name of the file we are processing
    :param anchor_key: The field we are matching
    :param found_keys: The list that contains the summary of keys found
    :param ocr_text: The current ocr line/word
    :param page: The page the items were found on
    :param height: The height attributes of the page
    :param width: The width attributes of the page
    :return: The appended json dict and the found keys list
    """

    found_keys.append(anchor_key)
    keys[blobname].append({
        'page': page,
        'height': height,
        'width': width,
        anchor_key: ocr_text,
        'BoundingBox': ocr_boundingbox
    })

    return keys, found_keys


def find_anchor_keys_in_form(anchor_keys, df_gt, filename, data, pass_number):
    """
    This function exists as part of the auto-labelling process for the supervised
    training. In essence, we strip whitespaces, punctuation and concatenate both the
    OCR and the Ground Truth and match.

    We do both a word pass and a higher line level pass as we can get better results for some forms
    depending on the layout. This is now demo code, see the full implementation here:
    https://github.com/microsoft/knowledge-extraction-recipes-forms/tree/master/Training/Auto_Labelling

    :param df_gt: The ground truth dataframe
    :param filename: The name of the file that we are processing
    :param data: The OCR for the record in question
    :param pass_number: An int that represents the pass number
    :return: A json object with the fields and corresponding bounding boxes
    """
    try:
        keys = {}
        i = 0
        keys[filename] = []
        found_keys = []
        # TODO add your unique file identifier here
        df_issuer_gt = df_gt[df_gt['FILENAME'] == str(filename[:len(filename) - 9])]

        # Now we loop through the anchor_keys to see if we can find them
        for anchor_key in anchor_keys:
            found_key = False

            no_strip = False
            anchor_key = anchor_key.strip()
            # Let's make sure the ground truth is indeed populated
            if len(df_issuer_gt[anchor_key]) == 0:
                continue

            for pages in data['analyzeResult']['readResults']:  # Added page
                if found_key:
                    break

                page = pages['page']
                height = pages['height']
                width = pages['width']
                for lines in pages['lines']:
                    if found_key:
                        break

                    # We operate at the lowest level where we can
                    for words in lines['words']:
                        if found_key:
                            break

                        ocr_clean_word = ''
                        ocr_clean_line = ''
                        gt_clean = ''

                        if anchor_key == 'BILL_TO':
                            # TODO add your custom formatting here - for the demo we just add text typical to the
                            # TODO invoice format. In reality you would use a classification approach from your master
                            # TODO record to identify vendors and bill to parties
                            # TODO See https://github.com/microsoft/knowledge-extraction-recipes-forms/blob/master/Analysis/Attribute_Search_Classification/README.md
                            gt_clean = 'Invoice for:' + str(df_issuer_gt[anchor_key].iloc[0])
                            gt_clean = strip_lower_remove_punctuation(
                                gt_clean.encode('ascii', 'ignore').decode('ascii'))

                        if anchor_key == 'TOTAL':
                            # TODO add custom total formatting here
                            gt_clean = df_issuer_gt[anchor_key].iloc[0]
                            ocr_clean_word = words['text'].replace(",", "")
                            ocr_clean_line = lines['text'].replace(",", "")
                            no_strip = True

                        if not no_strip:

                            # Now we clean out all punctuation for exact matching - word level
                            if len(ocr_clean_line) == 0:
                                ocr_clean_line = strip_lower_remove_punctuation(
                                    lines['text'].encode('ascii', 'ignore').decode('ascii'))
                            else:
                                ocr_clean_line = strip_lower_remove_punctuation(
                                    ocr_clean_line.encode('ascii', 'ignore').decode('ascii'))

                            # Now we clean out all punctuation for exact matching - line level
                            if len(ocr_clean_word) == 0:
                                ocr_clean_word = strip_lower_remove_punctuation(
                                    words['text'].encode('ascii', 'ignore').decode('ascii'))
                            else:
                                ocr_clean_word = strip_lower_remove_punctuation(
                                    ocr_clean_word.encode('ascii', 'ignore').decode('ascii'))

                            if len(gt_clean) == 0:
                                gt_clean = strip_lower_remove_punctuation(
                                    str(df_issuer_gt[anchor_key].iloc[0]).encode('ascii', 'ignore').decode('ascii'))

                            gt_clean = gt_clean.replace(" ", "")
                            ocr_clean_word = ocr_clean_word.replace(" ", "")
                            ocr_clean_line = ocr_clean_line.replace(" ", "")

                        if len(gt_clean) > 0:
                            if gt_clean == ocr_clean_word:
                                print('Matched', gt_clean, ocr_clean_word, anchor_key, filename)
                                ocr_orig_word = words['text']

                                keys, found_keys = build_keys_json_object(keys, filename,
                                                                          anchor_key, found_keys,
                                                                          ocr_orig_word,
                                                                          words['boundingBox'],
                                                                          page,
                                                                          height,
                                                                          width)
                                found_key = True


                            elif (gt_clean == ocr_clean_line) and (pass_number == 2):
                                print('Matched', gt_clean, ocr_clean_line, anchor_key, pass_number, filename)
                                ocr_orig_line = lines['text']
                                keys, found_keys = build_keys_json_object(keys, filename,
                                                                          anchor_key, found_keys,
                                                                          ocr_orig_line,
                                                                          lines['boundingBox'],
                                                                          page,
                                                                          height,
                                                                          width)
                                found_key = True

                            #  TODO catch all here
                            elif (gt_clean in ocr_clean_line) and ((anchor_key == 'BILL_TO_ZIP') or
                                                                   anchor_key == 'VENDOR_ZIP'):
                                ocr_orig_line = lines['text']
                                keys, found_keys = build_keys_json_object(keys, filename,
                                                                          anchor_key, found_keys,
                                                                          ocr_orig_line,
                                                                          lines['boundingBox'],
                                                                          page,
                                                                          height,
                                                                          width)
                                found_key = True

        i += 1

    except Exception as e:
        exc_type, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(f'Labelling error {e} {exc_type} {fname} {exc_tb.tb_lineno}')

    return keys


def is_phrase_in(ocrword, source_text):
    """

    :param ocrword: The OCR word we have potentially cleaned
    :param source_text: The full OCR text we have cleaned
    :return: True if found
    """
    if source_text.find(ocrword) > -1:
        return True
    return False


def compute_partial_ratio(source, target):
    """

    :param source: The source word
    :param target: The target word
    :return: Computes the ratio between source and target returns an int
    """
    score = fuzz.partial_ratio(target, source)
    return score


def compute_ratio(source, target):
    """

    :param source: The source word
    :param target: The target word
    :return: Computes the ratio between source and target returns an int
    """
    score = fuzz.ratio(target, source)
    return score


def date_format(text):
    """

    :param text: The input date text to format
    :return: A consistently formatted date
    """
    has_characters = re.compile(r'[a-zA-Z]')
    date = date_patterns(text)
    if date:
        try:
            formatted = moment.date(date).date

            if not re.search(has_characters, date):
                day = formatted.day
                if day < 13:
                    formatted = datetime.datetime(formatted.year, formatted.day, formatted.month)
            return formatted.strftime('%d%m%Y')
        except ValueError:
            print(f'Could not parse: {date}')
            return ''
    else:
        return ''


def date_patterns(text):
    """
    Given source text look for
    matches for each date pattern within the text and print
    them to stdout.
    """

    matches = text
    # TODO add any custom date regex patterns here
    return matches


def iban_patterns(text, length):
    """

    :param text: The input Iban text
    :return: The masked text
    """
    mask = []
    # TODO add any custom masks here - examples below
    if length == 11:
        mask.append('{}{} {}{}{} {}{}{}{} {}{}'.format(*text).lower())

    if length == 6:
        mask.append('00' + text)

    if length == 7:
        mask.append('0' + text)

    return mask


def vat_patterns(text, length):
    """

    :param text: The input vat text
    :return: The masked text
    """
    mask = []
    # TODO add any custom masks here - examples below

    if length == 9:
        mask.append('{}{}{} {}{}{}{} {}{}'.format(*text).lower())
        mask.append('{}{}{} {}{}{} {}{}{}'.format(*text).lower())

    if length == 11:
        mask.append('{}{} {}{}{} {}{}{}{} {}{}'.format(*text).lower())

    return mask


def fuzzy_digit_matching(identifier, digit_block_text):
    """

    :param identifier: The digits to be found in the block of text
    :param digit_block_text: The digit-only text to be scanned
    :return: True if matched with high confidence
    """
    cleanidentifier = re.sub("[^0-9]", "", identifier)
    # Slice text block into length of identifier to get candidates
    slices = [digit_block_text[i:i + len(cleanidentifier)] for i in range(0, len(digit_block_text))]
    # Get highest matching slice
    highest = process.extractOne(cleanidentifier, slices, scorer=fuzz.ratio)
    # Check if highest match is relevant
    if highest[1] > 75:  # TODO find an acceptable threshold
        return True
    return False


def handle_date(text_date, country_code):
    """

        :param date_text:
        :param language_code:
        :return: The formatted date ready for the next level of formatting
        """
    gt_date = text_date + country_code
    # TODO implement your custom date formatting to normalise your Ground Truth format

    return gt_date


def handle_number_extraction(number_text):
    """
    You custom number formatting here
    :param number_text:
    :return:
    """

    processed = number_text
    # TODO implement your custom number formatting
    return processed


def handle_date_format_num_word_num(date_text, country_code):
    """

    :param date_text:
    :param language_code:
    :return: The formatted date ready for the next level of formatting
    """
    new_ocr_date = date_text + country_code
    # TODO implement your custom date formatting
    return new_ocr_date


def resize_image(DATA_PATH, file_name, size):
    """
    This will resize an image
    :param DATA_PATH: The path to the files
    :param file_name: The filename
    :param size: Size to scale by 200, 300 etc
    :return: The resized image
    """
    roi = cv2.imread(os.path.join(DATA_PATH, file_name))
    scale_percent = size  # percent of original size
    width = int(roi.shape[1] * scale_percent / 100)
    height = int(roi.shape[0] * scale_percent / 100)
    dim = (width, height)
    resized = cv2.resize(roi, dim, interpolation=cv2.INTER_AREA)

    return resized


def score_and_rank(active_file, GT, result, best_score):
    """
    Function used by the remove boxes demo
    :param active_file: The image file we are assessing
    :param GT: The ground truth string
    :param result: The OCR result string
    :param best_score: The dict containing the scores
    :return: best_score dict, top_score (sorted best_score)
    """
    par_score = compute_partial_ratio(GT, get_text_from_ocr(result))
    score = compute_ratio(GT, get_text_from_ocr(result))
    best_score[active_file] = (par_score + score) / 2
    top_score = sorted(best_score.items(), key=lambda x: x[1], reverse=True)

    print(f"{active_file} Score {(par_score + score) / 2}")
    print(f"GT: {GT} OCR: {get_text_from_ocr(result)}")
    print(f"\n-----Best performing images----------")
    for rank, file in enumerate(top_score):
        print(f" {rank}: {file[0]} {file[1]}")

    return best_score, top_score


def apply_erosion(DATA_PATH, file_name, erosion_size=1):
    """
    This function will apply erosion to a file
    :param DATA_PATH: The path to the files
    :param file_name: The image we are processing
    :param erosion_size: The size of the erosion
    :return: filename - The file is saved to disk
    """
    src = cv2.imread(os.path.join(DATA_PATH,  file_name))

    erosion_type = 0
    erosion_type = cv2.MORPH_RECT
    element = cv2.getStructuringElement(erosion_type, (2 * erosion_size + 1, 2 * erosion_size + 1),
                                        (erosion_size, erosion_size))
    erosion_dst = cv2.erode(src, element)
    cv2.imwrite(os.path.join(DATA_PATH + file_name[:-4] + str(erosion_size) + '_eroded.jpg'), erosion_dst)
    return file_name[:-4] + str(erosion_size) + '_eroded.jpg'


def apply_dilatation(DATA_PATH, file_name, dilatation_size=1):
    """
    This function will apply dilatation to a file
    :param DATA_PATH: The path to the files
    :param file_name: The image we are processing
    :param dilatation_size_size: The size of the dilatation
    :return: filename - The file is saved to disk
    """
    src = cv2.imread(os.path.join(DATA_PATH,  file_name))

    dilatation_type = 0

    dilatation_type = cv2.MORPH_RECT
    element = cv2.getStructuringElement(dilatation_type, (2*dilatation_size + 1, 2*dilatation_size+1), (dilatation_size, dilatation_size))
    dilatation_dst = cv2.dilate(src, element)
    cv2.imwrite(os.path.join(DATA_PATH + file_name[:-4] + str(dilatation_size) + '_dilatation.jpg'), dilatation_dst)

    return file_name[:-4] + str(dilatation_size) + '_dilatation.jpg'


def get_projection(image, vert=False):
    """
    Applies projection to an image
    :param image: The image we are assessing
    :param vert:
    :return:
    """

    axis = 1
    if vert:
        axis = 0

    # Compute the sums of the rows - the projection
    # row_sums = sum_rows(image)
    row_sums = np.sum(image, axis=axis)

    # normalise to 0 to 255
    max_row = np.max(row_sums)
    row_sums = (row_sums / max_row) * 255
    return row_sums


def load_image(DATA_PATH, file_name, squarify=False, invert=True):
    """
    Loads an image and inverts
    :param DATA_PATH: The path to the files
    :param file_name: The image we are processing
    :param squarify: Extract square coords
    :param invert: Boolean to invert
    :return: The image
    """

    img = cv2.imread(os.path.join(DATA_PATH, file_name), 0)

    if invert:
        img = 255 - img

    if squarify:
        h, w = img.shape
        min_dim = min(h, w)
        img = img[0:min_dim, 0:min_dim]

    return img


def find_runs(sum_rows, level=0):
    """
    Identify sequence of rows where the sum is high.
    This indicates existence of text (where the sum is above level)
    Do the same for sequences where the sum is low
    This indicates a line break - the abscence of text
    """
    lows = []
    highs = []
    num_rows = len(sum_rows)
    old_low_high = -1
    curr_run = []

    for pos in range(num_rows):

        if sum_rows[pos] <= level:
            low_high = 0
        else:
            low_high = 1

        if old_low_high == -1:
            old_low_high = low_high
            curr_run.append(pos)
            continue

        if old_low_high != low_high:
            # new run
            if old_low_high == 0:
                lows.append(curr_run)
            else:
                highs.append(curr_run)

            old_low_high = low_high
            curr_run = []

        curr_run.append(pos)

    return lows, highs


def analyze_runs(lows):
    """
    Analyses projection runs
    :param lows:
    :return: start, end, median_width, lmr_low
    """

    print("lows")
    lmr_low = []
    for run in lows:
        middle_of_run = ((run[-1] - run[0])/2) + run[0]
        run_width = run[-1] - run[0]
        lmr_low.append([run[0], middle_of_run, run[-1], run_width])

        print(f"num points: {len(run)}"
              f" run_width: {run_width}"
              f" middle pos of run: {middle_of_run}")

    # extract details of each 'low' - start, middle, end, width
    widths = []
    num_seqs = len(lmr_low)
    prev_lmr = None
    for i in range(num_seqs):
        lmr = lmr_low[i]
        if prev_lmr is None:
            prev_lmr = lmr_low[i]
            continue

        pl, pm, pr, pw = prev_lmr
        l, m, r, w = lmr

        widths.append(m-pm)
        prev_lmr = lmr

    median_width = np.median(widths)

    start = lmr_low[0][1]
    end = lmr_low[-1][1]

    return start, end, median_width, lmr_low
