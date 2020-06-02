import os
import re
import string

import sys

sys.path.insert(1, '../../common/')

from common.common import date_format, handle_date_format_num_word_num


def sum_bounding_box(bbox):
    """

    :param bbox: Bounding box of the associated text
    :return: A single int
    """
    return sum(bbox)


def return_top200_as_dataframe(gt_dataframe):
    """

    :param gt_dataframe: The ground truth pandas dataframe
    :return: Filtered to the top200 records in terms of vendor frequency in invoice totale
    """

    frequency_dataframe = gt_dataframe['CoFiCoVendorNumber'].value_counts() / len(gt_dataframe)
    top200 = gt_dataframe[gt_dataframe['CoFiCoVendorNumber'].isin(frequency_dataframe[:200].index)]

    return top200


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


def find_anchor_key_in_invoice_text(df_vendor_gt, df_ocr, row):
    """

    :param df_vendor_gt: The vendor gt file
    :param df_ocr: A dataframe contaning the OCR scan of the invoice
    :param row: Active dataframe current row from outside loop
    :return: Equal length lists that will be used to construct the vendor cluster dataframe
    """
    lst_files = []
    lst_vendornames = []
    lst_bbox_area = []
    lst_bbox_par = []
    lst_bbox_line = []
    lst_bbox_page = []
    lst_anchor_key = []
    lst_page = []

    # We will anchor from a few key fields we want to assess
    anchor_keys = ['InvoiceNumber', 'InvoiceDate', 'NetValue', 'TaxValue', 'TotalAmount',
                   'PurchaseOrder']

    for anchor_key in anchor_keys:

        for row_ocr in enumerate(df_ocr.itertuples(), 1):
            if len(df_vendor_gt[anchor_key]) == 0:
                continue

            if anchor_key == 'InvoiceDate':
                ocr_clean = date_format(row_ocr[1].data_word)
                gt_clean = date_format(
                    str(df_vendor_gt[anchor_key].iloc[0]).encode('ascii', 'ignore').decode(
                        'ascii'))
            else:
                ocr_clean = strip_lower_remove_punctuation(
                    row_ocr[1].data_word.encode('ascii', 'ignore').decode('ascii'))
                gt_clean = strip_lower_remove_punctuation(
                    str(df_vendor_gt[anchor_key].iloc[0]).encode('ascii', 'ignore').decode('ascii'))

            if ocr_clean == gt_clean:
                print('Found', ocr_clean, 'GT:', gt_clean, anchor_key)
                lst_vendornames.append(row[12])  # row.vendor
                lst_files.append(row[47])  # row.file
                lst_page.append(row_ocr[1].page)
                lst_bbox_area.append(sum_bounding_box(row_ocr[1].bbox_area))
                lst_bbox_page.append(sum_bounding_box(row_ocr[1].bbox_page))
                lst_bbox_par.append(sum_bounding_box(row_ocr[1].bbox_par))
                lst_bbox_line.append(sum_bounding_box(row_ocr[1].bbox_line))
                # lst_bbox_total.append(sum_bounding_box(row_ocr[1].bbox_area)+
                #                      sum_bounding_box(row_ocr[1].bbox_par)+
                #                     sum_bounding_box(row_ocr[1].bbox_word))
                lst_anchor_key.append(anchor_key)
                break

    data = {'vendor': lst_vendornames, 'file': lst_files, 'key': lst_anchor_key, 'page': lst_page,
            'bbox_area': lst_bbox_area, 'bbox_para': lst_bbox_par, 'bbox_line': lst_bbox_line,
            'bbox_page': lst_bbox_page}

    return data


def add_trailing_zero(df_vendor_gt, anchor_key):
    """
    This function will amend the single temporary ground truth data frame record at runtime
    :param df_vendor_gt: The single temporary ground truth data frame record
    :param anchor_key: The field we are currently processing
    :return: The amended dataframe
    """

    idx = str(df_vendor_gt[anchor_key].iloc[0]).find(".")
    if len(str(df_vendor_gt[anchor_key].iloc[0])[idx + 1:]) == 1:
        df_vendor_gt[anchor_key].iloc[0] = str(df_vendor_gt[anchor_key].iloc[0]) + '0'

    return df_vendor_gt


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


def find_anchor_keys_in_form(df_gt, filename, data, anchor_keys, pass_number):
    """
    This function exists as part of the auto-labelling process for the supervised
    training

    :param df_gt: The ground truth dataframe
    :param filename: The name of the file that we are processing
    :param data: The OCR for the record in question
    :param pass_number: An int that represents the pass number
    :param anchor_keys: The fields we want to extract - passed in from the ENV file
    :return: A json object with the fields and corresponding bounding boxes
    """

    try:

        keys = {}
        i = 0
        keys[filename] = []
        found_keys = []
        # Your anchor_keys (key_field_names) should like like the sample list below
        # anchor_keys = ['InvoiceNumber', 'InvoiceDate', 'NetValue', 'TaxValue', 'TotalAmount']

        df_vendor_gt = df_gt[df_gt['FILENAME'] == str(filename[:len(filename) - 13])]
        # TODO Page 0 only at the moment - may need to be changed
        page = data['analyzeResult']['readResults'][0]['page']
        height = data['analyzeResult']['readResults'][0]['height']
        width = data['analyzeResult']['readResults'][0]['width']

        # Now we loop through the anchor_keys to see if we can find them
        for anchor_key in anchor_keys:
            # Let's make sure the ground truth is indeed populated
            if len(df_vendor_gt[anchor_key]) == 0:
                continue

            for pages in data['analyzeResult']['readResults']:  # Added page

                page = pages['page']
                height = pages['height']
                width = pages['width']
                for lines in pages['lines']:
                    # for lines in data['analyzeResult']['readResults'][0]['lines']:
                    # We operate at the lowest level where we can
                    for words in lines['words']:

                        ocr_clean_word = ''
                        ocr_clean_line = ''
                        gt_clean = ''

                        if anchor_key == 'NetValue':
                            # Handle your formatting value here
                            ocr_clean_word = ''

                        if anchor_key == 'TotalAmount':
                            # Handle your formatting value here
                            ocr_clean_word = ''

                        if anchor_key == 'InvoiceDate':
                            # Handle your date formatting here
                            gt_clean = date_format(
                                str(df_vendor_gt[anchor_key].iloc[0]).encode('ascii', 'ignore').decode(
                                    'ascii'))

                            ocr_clean_word = handle_date_format_num_word_num(words['text'])
                            # Apply to one level up as well
                            ocr_clean_line = handle_date_format_num_word_num(lines['text'])

                            # This can fail if out string is not a date due to some unhandled format
                            try:
                                ocr_clean_word = date_format(ocr_clean_word)
                                ocr_clean_line = date_format(ocr_clean_line)
                            except Exception:
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
                            str(df_vendor_gt[anchor_key].iloc[0]).encode('ascii', 'ignore').decode('ascii'))

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
        print('Error', e, exc_type, fname, exc_tb.tb_lineno)

    return keys
