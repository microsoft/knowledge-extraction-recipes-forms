import os
import pandas as pd
from common.common import find_anchor_key_in_form_text
from dotenv import load_dotenv


load_dotenv()


class Config:
    """
    Read from .env file
    """
    ANCHOR_KEYS = os.environ.get("ANCHOR_KEYS")  # The fields we want to find
    GROUND_TRUTH_FILE_PATH = os.environ.get("GROUND_TRUTH_FILE_PATH")  # Path to your GT file
    BBOX_FILE = os.environ.get("BBOX_FILE")  # The output file and path to write to
    DEVIATIONS_FILE = os.environ.get("DEVIATIONS_FILE")  # The output file and path to write to


def main():
    """

    :param: See Config class which reads from .env file
    :return: Generates cluster file
    """
    anchor_keys = Config.ANCHOR_KEYS.split(",")

    # TODO - Connect to your data source here

    # TODO - Load your GT file here
    ground_truth_forms = pd.DataFrame(Config.GROUND_TRUTH_FILE_PATH)

    for i, row in enumerate(ground_truth_forms.itertuples()):

        # TODO - Now we load the OCR for the form being processed
        filepath = ['The path to your OCR']

        data = {'formname': [], 'file': [], 'key': [], 'page': [], 'bbox_area': [],
                'bbox_para': [], 'bbox_line': [], 'bbox_page': []}

        try:
            with open(filepath, 'rb') as ocr:
                # TODO - Read the ocr file - this example uses a dataframe
                df_ocr = ocr.read()
                # TODO - now filter the ground truth data frame
                df_single_form_gt = ['Filtered to single record for the single form']

                # This function will now try to find the anchor keys and return coordinates
                inv_data = find_anchor_key_in_form_text(df_single_form_gt, df_ocr, row, anchor_keys)

                # add inv anchor keys to dictionary of all invoices
                for key, value in inv_data.items():
                    data[key].extend(value)

        except Exception as filenotfounderr:
            print(filenotfounderr)
            continue

    # Save data
    dfcluster = pd.DataFrame(data)
    dfcluster.to_csv(Config.BBOX_FILE, sep=',')

    lst_vendornames = []
    lst_bbox_area = []
    lst_bbox_par = []
    lst_bbox_line = []
    lst_bbox_page = []
    lst_anchor_key = []

    # TODO - add your key here Your_key
    keyset = list(set(dfcluster.Your_key))

    for key in keyset:
        for anchor_key in anchor_keys:
            df_single_form_gt = dfcluster[
                # TODO - add your form key here
                (dfcluster['formname'] == key) & (dfcluster['key'] == anchor_key)]

            lst_vendornames.append(key)
            lst_anchor_key.append(anchor_key)
            lst_bbox_area.append(df_single_form_gt['bbox_area'].describe()[2])
            lst_bbox_par.append(df_single_form_gt['bbox_para'].describe()[2])
            lst_bbox_line.append(df_single_form_gt['bbox_line'].describe()[2])
            lst_bbox_page.append(df_single_form_gt['bbox_page'].describe()[2])

    data = {'vendor': lst_vendornames, 'key': lst_anchor_key, 'bbox_area_std': lst_bbox_area,
            'bbox_para_std': lst_bbox_par, 'bbox_line_std': lst_bbox_line, 'bbox_page_std': lst_bbox_page}
    dfcluster = pd.DataFrame(data)

    dfcluster.to_csv(Config.DEVIATIONS_FILE, sep=',')
    print(f'Wrote deviations file {Config.DEVIATIONS_FILE}')


if __name__ == "__main__":
    main()
