import json
import os
import sys

import numpy as np
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


def load_json(file_path):
    """

    :param file_path: path to file
    :return: The json loaded
    """
    with open(file_path) as json_file:
        data = json.load(json_file)
    return data


def save_json(data, output_file_path):
    """

    :param data: To data to write
    :param output_file_path: The path to write
    :return: Nothing
    """
    with open(output_file_path, 'w') as out_file:
        json.dump(data, out_file, indent=4)


def get_issuer_key_field_accuracy(issuer_results, key_fields, ground_truth_df):
    """
    Get the accuracy of each field
    :param issuer_results: the prediction result file contents
    :param key_fields: the fields to evaluate
    :return: dictionary keyed by field name, value is field accuracy
    """

    acc = {k: 0.0 for k in key_fields}

    results = get_issuer_histogram(issuer_results, key_fields, ground_truth_df)

    num_invoices = len(issuer_results.keys())

    for key_field in key_fields:
        total_matches = results[key_field]
        acc[key_field] = total_matches / num_invoices

    return acc


def get_issuer_aggregated_accuracy(issuer_results, key_fields, ground_truth_df):
    """
    Calculate the scalar accuracy figure for a form issuer
    :param issuer_results: the prediction results json file contents
    :param key_fields: the fields to evaluate
    :return: scalar accuracy of the issuer, scalar accuracy (excludes
             missing fields)
    """

    results = get_issuer_histogram(issuer_results, key_fields, ground_truth_df)
    num_forms = len(issuer_results.keys())
    num_fields = num_forms * len(key_fields)

    total_aggregated_matches = 0
    total_num_keys_found = 0
    for key_field in key_fields:
        num_found, num_correct = results[key_field]
        total_matches_for_field = num_correct
        total_aggregated_matches += total_matches_for_field
        total_num_keys_found += num_found

    # Includes where no field was found - all possible matches
    overall_accuracy = 0
    if num_fields > 0:
        overall_accuracy = total_aggregated_matches / num_fields
    # Only where the field was found - excludes missing
    # This is useful to know
    accuracy_of_extracted_fields = 0
    if total_num_keys_found > 0:
        accuracy_of_extracted_fields = total_aggregated_matches / total_num_keys_found

    return overall_accuracy, accuracy_of_extracted_fields


def get_issuer_key_extraction_rate(issuer_results, key_fields):
    """
    Identify the extraction accuracy by field name.
    :param issuer_results: The prediction results for the issuer
    :param key_fields: The fields to evaluate
    :return: The count of extracted fields, the count of correct reads
    """

    key_counts = np.zeros(len(key_fields) + 1, dtype=np.int)
    correct_key_counts = np.zeros(len(key_fields) + 1, dtype=np.int)

    for file_name in issuer_results.keys():

        invoice_results = issuer_results[file_name]

        found_keys = []
        found_correct_keys = []
        for key_result in invoice_results:

            key = key_result['key']
            if key not in key_fields:
                continue

            # Store how many keys were found
            found_keys.append(key)

            # Store how many found that are correct
            gt_value, extracted_value, _ = get_key_values(key, key_result)
            if gt_value == extracted_value:
                found_correct_keys.append(key)

        key_counts[len(found_keys)] += 1
        correct_key_counts[len(found_correct_keys)] += 1

    return key_counts, correct_key_counts


def pre_process_gt(key_field, gt):
    """
    Convert the ground truth value for
    comparison to the extracted value from the document.
    :param key_field: the field name
    :param gt: the ground truth value
    :return:
    """

    # TODO add logic here for multi-page fields
    if key_field in Config.MULTI_PAGE_FIELDS.split():
        if not isinstance(gt, str):
            gt = "{:.2f}".format(gt)

    if not isinstance(gt, str):
        gt = str(gt)

    # TODO apply any custom formatting logic here
    if key_field == 'FormNumber':
        gt = gt.upper()

    return gt


def post_process(key_field, extracted):
    """
    Convert the field values for matching with the ground truth.
    :param key_field: The field name
    :param extracted: The value extracted from the document
    :return: The post processed extracted value
    """

    # TODO - apply any custom formatting here e.g.
    if key_field == 'FormNumber':
        extracted = extracted.upper()
        extracted = extracted.strip("$")
        extracted = extracted.replace("-", "")

    return extracted


def get_key_values(key_field, key_results):
    """
    Extract the ground truth and extracted value
    from the prediction results
    :param key_field: The field name
    :param key_results: The prediction result for the field
    :return: ground truth, the extracted value and float confidence score
    """

    gt_value = key_results['groundTruthValue']
    gt_value = pre_process_gt(key_field, gt_value)

    extracted_value = key_results['extractedValue']
    extracted_value = post_process(key_field, extracted_value)

    confidence = key_results['confidence']

    return gt_value, extracted_value, confidence


def get_page_number_field_histograms(issuer_results, key_fields):
    """
    Extract the page number the key field were extracted from
    :param issuer_results: The prediction results json file contents
    :param key_fields: The list of fields to consider
    :return: A dictionary keyed by field name.
    """

    results = {k: [0, 0] for k in key_fields}

    for file_name in issuer_results.keys():

        invoice_results = issuer_results[file_name]

        if len(invoice_results) == 0:
            # No keys found
            continue

        for key_results in invoice_results:

            for key_field in key_fields:
                key = key_results['key']
                if key == key_field:
                    # Get values after formatting corrections
                    gt_value, extracted_value = get_key_values(key_field, key_results)
                    # Field_page_num = key_results['pageNumber']

                    # Increment found key
                    results[key][0] += 1
                    if gt_value == extracted_value:
                        # Increment correct key
                        results[key][1] += 1


def get_issuer_histogram(issuer_results, key_fields, ground_truth_df):
    """
    Iterate the prediction results for a issuer counting
    how many correct results for each field, and how many
    fields were extracted.
    :param issuer_results:
    :param key_fields: List of the fields to consider
    :return: Dictionary keyed by field name containing
             the number of fields extracted and the number
             of fields that were correct
    """

    results = {k: [0, 0] for k in key_fields}

    for issuer_key in issuer_results.keys():

        form_results = issuer_results[issuer_key]

        for key_field in key_fields:
            key_found = False
            for key_results in form_results:
                if key_field == key_results['key']:
                    key_found = True
                    # Get values after formatting corrections
                    gt_value, extracted_value, _ = get_key_values(key_field, key_results)
                    # Increment found key
                    results[key_field][0] += 1
                    if gt_value == extracted_value:
                        # Increment correct key
                        results[key_field][1] += 1

            if key_found is False:
                if key_field in Config.MULTI_PAGE_FIELDS.split():
                    gt_value = get_gt_value(key_field, issuer_key, ground_truth_df)
                    if gt_value == 0:
                        results[key_field][0] += 1
                        results[key_field][1] += 1

    return results


def get_gt_value(key_field, issuer_key, ground_truth_df):
    """

    :param key_field: The field were are extracting and scoring
    :param issuer_key: The unique identifier for the form
    :param ground_truth_df: The dataframe container the Ground Truth
    :return: The single Ground Truth value
    """

    # Get short file name to query ground truth
    key_parts = issuer_key.split(':')
    issuer_id = key_parts[0]
    file_name = key_parts[1]
    # TODO add any customer search logic here

    short_file_name = ''
    # Get ground truth row
    # TODO add your custom file name identifier here
    df_gt_row = ground_truth_df[ground_truth_df['Your File Name'] == short_file_name]

    return df_gt_row[key_field].iloc[0]


def get_issuer_confidence_results(issuer_results, key_fields):
    """
    Build a list of confidence scores for each form and field
    for use in identifying false positives for a particular confidence level
    :param issuer_results: The json prediction results for a vendor
    :param key_fields: The list of key anchor fields to evaluate
    :return: Dictionary of keyed by fields with ground truth matches and confidence scores
    """

    results = {k: [] for k in key_fields}

    for file_name in issuer_results.keys():

        form_results = issuer_results[file_name]

        key_results = {key_result['key']: key_result for key_result in form_results}

        for anchor_key in key_fields:

            if anchor_key not in key_results:
                # Missing key
                results[anchor_key].append([-1, 0.0])
                continue

            key_result = key_results[anchor_key]
            gt_value, extracted_value, confidence = get_key_values(anchor_key, key_result)

            if gt_value == extracted_value:
                result = [1, confidence]
            else:
                result = [0, confidence]

            results[anchor_key].append(result)

    return results


def print_results(issuer_id, key_fields, issuer_results, output_file_name, ground_truth_df):
    """
    Retrieve and print the summary results of a vendor
    :param issuer_id: The issuer identifier
    :param key_fields: The list of fields to evaluate
    :param issuer_results: The loaded results produced by prediction
    :return: Average accuracy - agg_accuracy, Overall Form Number Accuracy FormNumberAccuracy
    """

    # TODO add the fields to be evaluated here e.g.
    FormNumberAccuracy = 0

    with open(os.path.join(Config.LOCAL_WORKING_DIR + output_file_name), "w") as output:

        results = get_issuer_histogram(issuer_results, key_fields, ground_truth_df)

        output.write(f"Issuer: {issuer_id}")
        output.write("\n")

        num_issuer_files = len(issuer_results.keys())
        output.write(f"total number of files: {num_issuer_files}")
        output.write("\n")
        output.write(f"Analysis of the following fields: {key_fields}")
        output.write("\n")

        agg_accuracy, acc_of_found_keys = get_issuer_aggregated_accuracy(issuer_results, key_fields, ground_truth_df)
        output.write(f"Overall issuer accuracy: {agg_accuracy:.2f}")
        output.write("\n")
        output.write(f"Accuracy of fields extracted (excludes missing fields): {acc_of_found_keys:.2f}")
        output.write("\n")
        output.write("=======")
        for k, v in results.items():
            num_extracted, num_matches = v
            found_acc = 0
            if num_extracted > 0:
                found_acc = num_matches / num_extracted

            # TODO add your custom field logic here
            if k == 'FormNumber':
                FormNumberAccuracy = 0
                if num_issuer_files > 0:
                    FormNumberAccuracy = num_matches / num_issuer_files

            temp_acc = 0
            if num_issuer_files > 0:
                temp_acc = num_matches / num_issuer_files
            output.write(f"Field: {k} Correct count: {num_matches} "
                         f"Accuracy: {temp_acc:.2f} "
                         f"num found: {num_extracted} Found acc: {found_acc:.2f}")
            output.write("\n")

        output.write("=======")
        output.write("\n")
        # Get key extraction rate
        key_counts, correct_key_counts = get_issuer_key_extraction_rate(issuer_results, key_fields)

        output.write(f"Distribution of extracted fields:")
        output.write("\n")
        for pos in range(len(key_counts)):
            output.write(f'    Num forms with {pos} extracted fields: {key_counts[pos]} ')
            output.write("\n")

        output.write(f"Distribution of correct extracted fields:")
        output.write("\n")
        for pos in range(len(correct_key_counts)):
            output.write(f'    Num forms with {pos} extracted fields: {correct_key_counts[pos]} ')
            output.write("\n")

        output.write(str(key_counts.tostring()))
        output.write("\n")
        output.write(str(key_counts.sum()))
        output.write("\n")
        output.write(str(correct_key_counts.tostring()))
        output.write("\n")
        output.write(str(correct_key_counts.sum()))
        output.write("\n")

        output.close()
        print('Wrote file', os.path.join(Config.LOCAL_WORKING_DIR + output_file_name))

    return agg_accuracy, FormNumberAccuracy


class Config:
    """
    Read from .env
    """
    RUN_FOR_SINGLE_ISSUER = os.environ.get("RUN_FOR_SINGLE_ISSUER")  # If true process only this issuer
    LOCAL_WORKING_DIR = os.environ.get("LOCAL_WORKING_DIR")  # The local directory where the results files are located
    ADLS_ACCOUNT_NAME = os.environ.get("ADLS_ACCOUNT_NAME")  # Data lake account
    ADLS_TENANT_ID = os.environ.get("ADLS_TENANT_ID")  # Azure AD tenant id
    GROUND_TRUTH_PATH = os.environ.get("GROUND_TRUTH_PATH")  # This is the path to our Ground Truth
    MULTI_PAGE_FIELDS = os.environ.get("MULTI_PAGE_FIELDS")  # These fields appear over multiple pages
    # and as such are handled differently. Typically totals fields on an invoice
    ANCHOR_KEYS = os.environ.get("ANCHOR_KEYS")  # The fields we want to extract


def get_ground_truth():
    """
    TODO Add code to retrieve the ground truth from your datastore

    :return: Data frame with the Ground Truth
    """

    df = None
    models_df = None

    try:

        # TODO load your Ground Truth file
        df = pd.read_pickle(Config.GROUND_TRUTH_PATH, compression=None)
        # TODO load your model/issuer lookup
        models_df = pd.read_csv(Config.MODEL_LOOKUP, delimiter=',', compression=None)

    except Exception as e:
        exc_type, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(f'Error loading files {e} {exc_type} {fname} {exc_tb.tb_lineno}')

    return df, models_df


def main():
    """
    Entry point
    :return: None
    """
    exclusion_list = [
        # TODO add any exclusions here if needed - these will not be evaluated
    ]

    overall_accuracy = 0
    accuracy = 0
    FormNumberAccuracy = 0
    overall_FormNumberAccuracy = 0

    # Get the ground truth file for the key value extraction
    ground_truth_df, models_df = get_ground_truth()

    rf = Config.LOCAL_WORKING_DIR
    if len(Config.RUN_FOR_SINGLE_ISSUER) > 0:
        print(Config.RUN_FOR_SINGLE_ISSUER)

        file_name = f'predict_{Config.RUN_FOR_SINGLE_ISSUER}_.json'
        issuer_result_file = f"{rf}{file_name}"
        key_fields = Config.ANCHOR_KEYS.split()

        # Get histogram of field results
        issuer_results = load_json(issuer_result_file)
        # TODO set your output file
        output_file_name = file_name[:-5] + '.txt'

        print_results(Config.RUN_FOR_SINGLE_ISSUER, key_fields, issuer_results, output_file_name, ground_truth_df)
    else:
        i = 0

        for file_name in os.listdir(rf):

            if file_name.endswith(".json"):

                issuer_name = file_name[18:-6]

                if issuer_name in exclusion_list:
                    print(f"Exclusion: {issuer_name}")
                    continue

                i += 1
                # TODO amend here to process your files
                file_name = f'predict_{issuer_name}_.json'
                issuer_result_file = f"{rf}{file_name}"
                key_fields = Config.ANCHOR_KEYS.split()

                # Get histogram of field results
                issuer_results = load_json(issuer_result_file)

                # TODO amend here for your outputs
                output_file_name = file_name[:-5] + '.txt'

                # TODO amend thus function to process all your fields
                accuracy, FormNumberAccuracy = print_results(Config.RUN_FOR_SINGLE_ISSUER,
                                                             key_fields, issuer_results,
                                                             output_file_name, ground_truth_df)

                print(accuracy, i)
                overall_accuracy += accuracy
                overall_FormNumberAccuracy += FormNumberAccuracy

        # TODO add your field reports here here
        print('Overall Accuracy', overall_accuracy / i, i)
        print('overall_InvoiceNumberAccuracy', overall_FormNumberAccuracy / i)


if __name__ == "__main__":
    main()
