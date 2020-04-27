import datetime
import os
import re
import string
import sys
from typing import List
from urllib.parse import quote

import moment  # type:ignore
import pandas as pd  # type:ignore
from fuzzywuzzy import fuzz, process  # type:ignore
from requests import get


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
    depending on the layout

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
        df_issuer_gt = df_gt[df_gt['Your file name'] == str(filename[:len(filename) - 13])]

        # Now we loop through the anchor_keys to see if we can find them
        for anchor_key in anchor_keys:
            # Let's make sure the ground truth is indeed populated
            if len(df_issuer_gt[anchor_key]) == 0:
                continue

            for pages in data['analyzeResult']['readResults']:  # Added page

                page = pages['page']
                height = pages['height']
                width = pages['width']
                for lines in pages['lines']:

                    # We operate at the lowest level where we can
                    for words in lines['words']:

                        ocr_clean_word = ''
                        ocr_clean_line = ''
                        gt_clean = ''

                        # TODO Add your Ground Truth value formatting here e.g.
                        if anchor_key == 'FormDate':  # TODO this is your field you want to extract
                            gt_clean = 'Normalise your Ground Truth field value'

                            ocr_clean_word = handle_date_format_num_word_num(words['text'])
                            # Apply to one level up as well
                            ocr_clean_line = handle_date_format_num_word_num(lines['text'])
                            # This can fail if out string is not a date due to some unhandled format
                            try:
                                # TODO add your custom field formatting here to both line and word
                                ocr_clean_word = 'Your custom formatting_function()'
                                ocr_clean_line = 'Your custom formatting_function()'

                                if len(ocr_clean_line) == 0:
                                    ocr_clean_line = lines['text']
                                    ocr_clean_word = words['text']

                                    # TODO try to fix some common errors add yours
                                    candidate_dates = ocr_clean_line.split("/")
                                    for candidate_date in candidate_dates:
                                        candidate_date = candidate_date.replace(" ", "")
                                        candidate_date = date_format(candidate_date)

                                if len(candidate_date) > 0:
                                    candidate_word = ocr_clean_word.replace("/", "")
                                    candidate_word = candidate_word.replace(" ", "")
                                    candidate_word = strip_lower_remove_punctuation(candidate_word)
                                    candidate_word = candidate_word.replace(" ", "")
                                    if (candidate_word in candidate_date) and (len(candidate_word) > 0):
                                        ocr_clean_word = candidate_date

                            except Exception as date_error:
                                print('Date handling error', ocr_clean_word, ocr_clean_line, date_error)
                                continue

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

                        gt_clean = strip_lower_remove_punctuation(
                            str(df_issuer_gt[anchor_key].iloc[0]).encode('ascii', 'ignore').decode('ascii'))

                        gt_clean = gt_clean.replace(" ", "")
                        ocr_clean_word = ocr_clean_word.replace(" ", "")
                        ocr_clean_line = ocr_clean_line.replace(" ", "")

                        if len(gt_clean) > 0:
                            if gt_clean == ocr_clean_word:
                                keys, found_keys = build_keys_json_object(keys, filename,
                                                                          anchor_key, found_keys,
                                                                          words['text'],
                                                                          words['boundingBox'],
                                                                          page,
                                                                          height,
                                                                          width)

                            elif (gt_clean == ocr_clean_line) and (pass_number == 2):
                                keys, found_keys = build_keys_json_object(keys, filename,
                                                                          anchor_key, found_keys,
                                                                          lines['text'],
                                                                          lines['boundingBox'],
                                                                          page,
                                                                          height,
                                                                          width)

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
