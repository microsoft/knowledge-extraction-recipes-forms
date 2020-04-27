import os
import pandas as pd  # type:ignore
from dotenv import load_dotenv

from common.common import build_deviations_file, build_max_differences_file, download

load_dotenv()


class Config:
    """
    Read from .env file
    """
    ANCHOR_KEYS = os.environ.get("ANCHOR_KEYS")  # The fields we want to find
    GROUND_TRUTH_FILE_PATH = os.environ.get("GROUND_TRUTH_FILE_PATH")  # Path to your GT file
    BBOX_FILE = os.environ.get("BBOX_FILE")  # The generated BBOX file
    DEVIATIONS_FILE = os.environ.get("DEVIATIONS_FILE")  # The generated deviations file
    OUTPUT_MAX_DIFF_FILE = os.environ.get("OUTPUT_MAX_DIFF_FILE")  # Output name
    OUTPUT_MAX_DIFF_PATH = os.environ.get("OUTPUT_MAX_DIFF_PATH")  # Output path
    THRESHOLD = os.environ.get("THRESHOLD")  # This is the threshold defined from the std deviation


def main(argv):
    """

    :param: See Config class which reads from .env file
    :return: Generates max diff file
    """

    # Let's load the files
    dfclusterbbox = pd.read_csv(Config.BBOX_FILE)
    dfclusterdev = pd.read_csv(Config.DEVIATIONS_FILE)

    anchor_keys = Config.ANCHOR_KEYS.split(",")

    # Here we build the deviations dataframe
    for anchor_key in anchor_keys:
        dfdev = build_deviations_file(dfclusterdev, Config.THRESHOLD, anchor_key)

        dfdev.to_csv(Config.DEVIATIONS_FILE[:-4] + '_' + anchor_key + '.csv', sep=',')
        print('Wrote mean file {}'.format(Config.OUTPUT_DEVIATIONS_FILE[:-4] +
                                          '_' + anchor_key + '.csv'))

    # Here we build the maximum differences datafile
    dfdfclusterbbox_maxmin = build_max_differences_file(dfclusterbbox, anchor_keys)
    dfdfclusterbbox_maxmin = dfdfclusterbbox_maxmin.sort_values('bbox_diff', ascending=False).drop_duplicates(
        subset='bbox_max_file').reset_index()

    dfdfclusterbbox_maxmin.to_csv(Config.OUTPUT_MAX_DIFF_FILE, sep=',')
    print(f'Wrote max differences file {Config.OUTPUT_MAX_DIFF_FILE}')

    box = 'bbox_line'
    if not os.path.isdir(os.path.join(Config.OUTPUT_MAX_DIFF_PATH, 'max_diffs_' + box)):
        os.mkdir(os.path.join(Config.OUTPUT_MAX_DIFF_PATH, 'max_diffs_' + box))

    # TODO now inspect the report files


if __name__ == "__main__":
    main()
