import os

import pandas as pd  # type:ignore
from dotenv import load_dotenv

from .common import find_vendor_in_invoice_text

load_dotenv()


class Config:
    """
    Read from .env file
    """
    ISSUERS_FILE_PATH = os.environ.get("ISSUERS_FILE_PATH")  # The attribute lookup file
    GROUND_TRUTH_FILE_PATH = os.environ.get("GROUND_TRUTH_FILE_PATH")  # Path to your GT file
    OUTPUT_FILE = os.environ.get("OUTPUT_FILE")  # The output file and path to write to
    DEVIATIONS_FILE = os.environ.get("DEVIATIONS_FILE")  # The output file and path to write to
    OCR_FILE_PATH = os.environ.get("OCR_FILE_PATH")  # The path to the OCR files
    NUMBER_OF_ATTRIBUTES = os.environ.get("NUMBER_OF_ATTRIBUTES")  # The number of attributes
    # search for - this is used to determine the end score


def main():
    """

    :param: See Config class which reads from .env file
    :return: Generates cluster file
    """

    # TODO - load your Ground Truth file as a dataframe if you need to evaluate the lookup accuracy
    gt_dataframe = Config.GROUND_TRUTH_FILE_PATH

    # TODO - load your attributes file here as a dataframe
    dfAttributes = pd.read_csv(Config.ISSUERS_FILE_PATH)

    print(f"Loaded attributes file")

    # TODO - create a list for each of the attributes to be searched for. These are outputted in
    # TODO a CSV file
    lst_files_csv = []
    lst_issuers_csv = []
    lst_issuer_zips_csv = []
    lst_issuer_numbers_csv = []
    lst_ibans_csv = []
    lst_score_csv = []
    lst_vat_csv = []
    not_found = 0
    search_term_issuer_found = 0

    for i, row in enumerate(gt_dataframe.itertuples(),
                            1):  # Standard for loop using input dict{} of files
        filepath = Config.OCR_FILE_PATH + str(row.FILENAME) + '.ocr.json'

        # TODO - depending on what OCR you use, load it here
        ocr_json = ['Your loaded OCR']

        print(f"Processing {filepath} row {i} of {len(gt_dataframe)}")

        # TODO - Read the ocr file - this example uses a dataframe
        df_ocr = ['ocr.read()']

        lst_files, lst_issuers, lst_issuer_zips, lst_ibans, \
        lst_score, lst_issuer_numbers, lst_vat, _, lst_city, search_term_issuer_found = \
            find_vendor_in_invoice_text(dfAttributes, df_ocr, str(row.FILENAME),
                                        filepath, search_term_issuer_found)

        # Now we rank and select the highest scoring vendor
        matched = {}
        # Zip by vendor number to avoid that vendors with same name are overwritten
        lst_vendor_score = zip(lst_issuer_numbers, lst_score)

        for vendor_number, score in lst_vendor_score:
            matched[str(vendor_number)] = int(score)

        # Let's get the best candidate
        if len(matched) > 0:
            best_match = max(matched.items(), key=lambda k: k[1])
            best_match_result = best_match[0]
            best_match_index = lst_issuer_numbers.index(best_match_result)
            print('Best match with total match score', lst_issuer_numbers[best_match_index],
                  str(int(best_match[1] / int(Config.NUMBER_OF_ATTRIBUTES))) + '%')
            lst_files_csv.append(lst_files[best_match_index])
            lst_issuers_csv.append(lst_issuers[best_match_index])
            lst_issuer_zips_csv.append(lst_issuer_zips[best_match_index])
            lst_score_csv.append(lst_score[best_match_index])
            lst_vat_csv.append(lst_vat[best_match_index])
            lst_issuer_numbers_csv.append(lst_issuer_numbers[best_match_index])

        # Spool in batches of 1000
        if i % 1000 == 0:
            data = {'issuer': lst_issuers,
                    'issuernumber': lst_issuer_numbers_csv,
                    'zip': lst_issuer_zips_csv, 'iban': lst_ibans_csv, 'vat': lst_vat_csv,
                    'score': lst_score_csv, 'file': lst_files_csv}
            dfcluster = pd.DataFrame(data)
            dfcluster.to_csv(Config.OUTPUT_FILE[:-4] + '_' + str(i) + '.csv', sep=',')
            print(f"Done - wrote cluster file {Config.OUTPUT_FILE[:-4] + '_' + str(i) + '.csv'}")

    print(f"Done: Found matches for {search_term_issuer_found} out of {len(gt_dataframe)}")


if __name__ == "__main__":
    main()
