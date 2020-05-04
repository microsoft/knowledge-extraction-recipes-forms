import logging
import os
import json
import pandas as pd
import numpy as np
from . import utils
from . import formatting

def find_anchor_keys_in_invoice(df_gt, filename, data, key_field_names, lookup_path, file_header='FileID'):
    """
    This function exists as part of the auto-labelling process for the supervised
    training
    :param df_gt: The ground truth dataframe
    :param filename: The name of the file that we are processing
    :param data: The OCR for the record in question
    :return: A json object with the fields and corresponding bounding boxes
    """
    try:
        keys = {}
        i = 0
        keys[filename] = []
        found_keys = []
        anchor_keys = key_field_names
        file_id = filename[:len(filename) - 4]
        df_file_gt = df_gt[df_gt[file_header] == file_id]

        found_fields = {}

        # Maximum number of pages to look at
        max_pages = 2

        # Looping through the keys to find
        for anchor_key in anchor_keys:

            columns = map_columns(anchor_key, lookup_path)

            # Matching keys with values from one or several columns in the GT
            final_text = ''
            final_bbox = ''
            found = False
            matching_page = 0

            compare_methods = []
            gt_values = []
            gt_processed = []

            # Trying to match all subfields to a line
            for col in columns:
                gt_val = ''
                try:
                    gt_val = str(df_file_gt[col].iloc[0])
                    gt_val = gt_val.split('\n')[0]
                    logging.info(f"Finding a match for value {gt_val}")
                except Exception as e:
                    logging.error(f"Could not get gt value: {e}")

                if utils.is_valid(gt_val):
                    compare_method = lookup_compare(col, lookup_path)
                    compare_methods.append(compare_method)
                    gt_values.append(gt_val)
                    gt_processed.append(formatting.normalize(gt_val, compare_method))
                else:
                    logging.warning(f"GT value not valid, skipping this field.")

            if len(gt_processed) > 0:

                matching_text = ''
                matching_bbox = ''

                occurence = 0

                for p in range(min(len(data['analyzeResult']['readResults']), max_pages)): 

                    for i in range(len(data['analyzeResult']['readResults'][p]['lines'])):

                        line = data['analyzeResult']['readResults'][p]['lines'][i]
                        if i < len(data['analyzeResult']['readResults'][p]['lines']) - 1:
                            next_line = data['analyzeResult']['readResults'][p]['lines'][i+1]
                        else:
                            next_line = ""


                        # Checking match for concatenated columns
                        # At line level if there's more than 1 column
                        # At word level as well if there's only 1
                        if len(gt_processed) > 1:
                            match, text, bbox = match_bbox(line, next_line, gt_processed, compare_methods, False)
                        else:
                            match, text, bbox = match_bbox(line, next_line, gt_processed, compare_methods)

                        if match == True:
                            gt_value = " ".join(v for v in gt_processed)
                            logging.info(f"MATCH FOR {anchor_key}: '{gt_value}' (GT) and '{text}' (document) - bbox {bbox}")

                            # We only add 0.5 because each occurence appears twice: once in the line and once in the next line
                            occurence += 0.5       

                            # If we already have found the field n times, we're looking for the (n+1)th occurence
                            try:
                                if found_fields[gt_value] >= occurence:
                                    n = found_fields[gt_value]
                                    logging.warning(f"Searching for occurence #{n+1}")
                                else:
                                    final_bbox = bbox
                                    final_text = text
                                    found = True
                                    matching_page = p
                                    break

                            # If we have never found it before, the value is not in found fields
                            except Exception:
                                final_bbox = bbox
                                final_text = text
                                found = True
                                matching_page = p
                                break

                    if found == True:
                        break

                # If no match for concatenated subfields, checking subfield by subfield
                if found == False and len(gt_processed) > 1:

                    logging.warning(f"No complete field match found, checking subfield by subfield")

                    occurence = 0

                    for i in range(len(gt_processed)):
                        
                        found = False
                        for p in range(min(len(data['analyzeResult']['readResults']), max_pages)): 
                            
                            for line in data['analyzeResult']['readResults'][p]['lines']:
                                match, text, bbox = match_bbox(line, "", [gt_processed[i]], [compare_methods[i]])
                                
                                if match == True:

                                    logging.info(f"MATCH FOR {columns[i]}: '{gt_processed[i]}' (GT) and '{line['text']}' (document) - bbox {bbox}")
                                    
                                    occurence += 1
                                    
                                    # If we already have found the field n times, we're looking for the (n+1)th occurence
                                    try:
                                        if found_fields[gt_processed[i]] >= occurence:
                                            n = found_fields[gt_processed[i]]
                                            logging.warning(f"Searching for occurence #{n+1}")
                                        else:
                                            matching_bbox = bbox
                                            matching_text = text
                                            found = True
                                            matching_page = p
                                            break

                                    # If we have never found it before, the value is not in found fields
                                    except Exception:
                                        matching_bbox = bbox
                                        matching_text = text
                                        found = True
                                        matching_page = p
                                        break

                            if found == True:
                                break

                        if(found == True):
                            final_text = final_text + matching_text + ' '
                            if final_bbox == '':
                                final_bbox = matching_bbox
                            else:
                                final_bbox = adjust_bbox(final_bbox, matching_bbox)

                if final_text != '':

                    page = data['analyzeResult']['readResults'][matching_page]['page']
                    height = data['analyzeResult']['readResults'][matching_page]['height']
                    width = data['analyzeResult']['readResults'][matching_page]['width']

                    final_text = formatting.remove_trailing_spaces(final_text)
                    logging.info(f"Match for {anchor_key}: {final_text} - bbox: {bbox}")

                    # Keeping track of the values we have already found
                    matching_gt_value = " ".join(val for val in gt_processed)
                    if matching_gt_value in found_fields:
                        found_fields[matching_gt_value] += 1
                    else:
                        found_fields[matching_gt_value] = 1
                    if len(gt_processed) > 1:
                        for val in gt_processed:
                            if val in found_fields:
                                found_fields[val] += 1
                            else:
                                found_fields[val] = 1
                
                    keys, found_keys = build_keys_json_object(keys, filename,
                                                                        anchor_key, found_keys,
                                                                        final_text,
                                                                        final_bbox,
                                                                        page,
                                                                        height,
                                                                        width)

                    i += 1
    except Exception as e:
        logging.error(f"Error finding anchor keys in invoice #{file_id}: {e}")

    return keys


def map_columns(key_name, lookup_path = "./lookup_fields.json"):
    lookup_fields = utils.get_lookup_fields(lookup_path)
    columns = []
    try:
        columns = lookup_fields['keys'][key_name]
        logging.info(f"Columns for field {key_name} are {str(columns)}.")
    except Exception as e:
        logging.error(f"Error looking up columns for field {key_name}: {e}")
    return columns

def lookup_compare(column_name, lookup_path = "./lookup_fields.json"):
    lookup_fields = utils.get_lookup_fields(lookup_path)
    compare_method = ""
    try:
        compare_method = lookup_fields["types"][column_name]
        logging.info(f"Compare method for field {column_name} is {compare_method}.")
    except Exception as e:
        logging.error(f"Error looking up compare method for field {column_name}: {e}")
    return compare_method

def match_bbox(line, next_line, gt_processed, compare_methods, wordlevel = True):

    compare_value = formatting.remove_trailing_spaces(" ".join(val for val in gt_processed))

    matching_text = ''
    matching_bbox = ''
    processed_text = formatting.remove_trailing_spaces(formatting.format_subfields(line['text'], compare_methods))
    
    # Match at line level
    if compare_value == processed_text:
        return True, line['text'], line['boundingBox']

    # Checking the next line as well
    if next_line != "":
        processed_text = formatting.remove_trailing_spaces(formatting.format_subfields(next_line['text'], compare_methods))
        if compare_value == processed_text:
            return True, next_line['text'], next_line['boundingBox']
        lines_text = line['text'] + " " + next_line['text']
        processed_text = formatting.remove_trailing_spaces(formatting.format_subfields(lines_text, compare_methods))
        if compare_value == processed_text:
            return True, line['text'] + ' ' + next_line['text'], adjust_bbox(line['boundingBox'], next_line['boundingBox'])
    
    # Match at word level
    if wordlevel == True:
        if compare_value in processed_text:
            # Checking if the value is present (will only work for regular text)
            matching_text = ""
            matching_bbox = ""
            lines_words = line['words']
            if next_line != "":
                lines_words += next_line['words']
            for word in lines_words:       
                word_processed = formatting.normalize(word['text'], compare_methods[0])
                if compare_value == word_processed:
                    return True, word['text'], word['boundingBox']
                elif word_processed in compare_value:
                    matching_text += word['text'] + " "
                    if(matching_bbox == ""):
                        matching_bbox = word['boundingBox']
                    else:
                        old_bbox = matching_bbox
                        matching_bbox = adjust_bbox(old_bbox, word['boundingBox'])
            if(matching_text != ""):
                return True, matching_text, matching_bbox
        else:
            # Checking if the value is present but formatted differently
            sub_text = formatting.find_subtext(line['text'],compare_methods[0])
            sub_text_processed = formatting.normalize(sub_text, compare_methods[0])
            sub_words = sub_text.split(" ")
            matching_text = ""
            matching_bbox = ""
            if compare_value == sub_text_processed:
                logging.warning(f"Sub words: {str(sub_words)} - Line words: {str(line['words'])}")
                for word in line['words']:
                    if word['text'] in sub_words:
                        matching_text += word['text'] + " "
                        if(matching_bbox == ""):
                            matching_bbox = word['boundingBox']
                        else:
                            old_bbox = matching_bbox
                            matching_bbox = adjust_bbox(old_bbox, word['boundingBox'])
                return True, matching_text, matching_bbox


    return False, "", ""

def adjust_bbox(o_bbox, w_bbox):
    try:
        bbox = o_bbox.copy()
        # [Point1 (x1, y1), Point2 (x2, y1), Point3 (x2, y2), Point4 (x1, y2)]
        # Moving Point2
        if w_bbox[2] > bbox[2]:
            bbox[2] = w_bbox[2]
            bbox[4] = w_bbox[4]
        if w_bbox[3] < bbox[3]:
            bbox[3] = w_bbox[3]
            bbox[1] = w_bbox[1]
        # Moving Point 3
        if w_bbox[4] > bbox[4]:
            bbox[4] = w_bbox[4]
            bbox[2] = w_bbox[2]
        if w_bbox[5] > bbox[5]:
            bbox[5] = w_bbox[5]
            bbox[7] = w_bbox[7]
        return bbox
    except Exception as e:
        logging.error(f"Error adjusting bbox: {e}")
        return o_bbox

def create_label_file(file_name, key_fields, key_field_details):
    """
    :param file_name: document file probably a PDF or TIF
    :param key_fields: the fields to extract from the OCR
    :param key_field_details: the extracted values extracted from the OCR
    """
    # create label file
    label_file = get_label_file_template(file_name)

    if label_file != None:

        # add key field values to the label file
        for key_field in key_fields:

            field_detail = get_key_field_data(key_field, key_field_details)
            if field_detail is None:
                continue

            page = field_detail['page']
            width = field_detail['width']
            height = field_detail['height']
            field_bounding_box = field_detail['BoundingBox']
            field_value = field_detail[key_field]

            #field_values = [field_value]  # if more than one bounding box.

            field = get_field_template(key_field)

            # convert to percentage coordinates
            polygon = convert_bbox_to_polygon(field_bounding_box, float(width), float(height))

            value = get_value_template(field_value, page, polygon)

            # add the key region to the field
            field['value'].append(value)

            # add the field to the doc template - each field is a 'label'
            label_file['labels'].append(field)

    print(f"Label file: {label_file}")

    return label_file


def analyze_labels(gt_path, file_path, analyze_result, key_field_names, lookup_path):

    gt_df = None
    try:
        if(type(gt_path).__name__ == "str"):
            gt_df = utils.load_excel(gt_path)
        else: gt_df = gt_path

        logging.info("Ground truth loaded.")
    except Exception as e:
        logging.error(f"Could not load ground truth: {e}")

    if len(gt_df) > 0:

        try:
            file_name = file_path.split('/')[-1]

            key_field_data = find_anchor_keys_in_invoice(
                gt_df,
                file_name,
                analyze_result,
                key_field_names,
                lookup_path)

            logging.info(f"key_field_data len: {str(len(key_field_data))}")

            label_file = create_label_file(
                file_path,
                key_field_names,
                key_field_data[file_name]
            )
            return label_file, key_field_data[file_name]

        except Exception as e:
            logging.error(f"Error analyzing labels: {e}")

    return None, None

def get_key_field_data(key_field, key_field_details):

    try:
        for field in key_field_details:
            if key_field in field:
                return field
    except Exception as e:
        logging.error(f"Error getting key field '{key_field}' data: {e}")

    return None

def get_label_file_template(doc_name):
    template = None
    try:
        template = {
            "document": doc_name.split('/')[-1],
            "labels": []
        }
    except Exception as e:
        logging.error(f"Error getting label file template: {e}")
    return template

def get_field_template(field_name):
    return {
        "label": field_name,
        "key": None,
        "value": []
    }

def get_value_template(value, page, region):
    v = {}
    v['page'] = page
    v['text'] = value
    v["boundingBoxes"] = [region]
    return v

def convert_bbox_to_polygon(bounding_box, width, height):
    """
    returns each coordinate as a percentage of the page size
    :param bounding_box: assumes format list: [x,y,x1,y1,x2,y2, ...]
    :param width: page width
    :param height: page height
    """
    try:
        if len(bounding_box) != 8:
            return None
        bounding_box = np.array(bounding_box)
        bounding_box[::2] /= width
        bounding_box[1::2] /= height
        return bounding_box.tolist()
    except Exception as e:
        logging.error(f"Could not convert bbox to polygon: {e}")
        return None

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

    try:
        found_keys.append(anchor_key)
        keys[blobname].append({
            'page': page,
            'height': height,
            'width': width,
            anchor_key: ocr_text,
            'BoundingBox': ocr_boundingbox
        })
        return keys, found_keys
    except Exception as e:
        logging.error(f"Error building keys json object: {e}")
        return None, found_keys