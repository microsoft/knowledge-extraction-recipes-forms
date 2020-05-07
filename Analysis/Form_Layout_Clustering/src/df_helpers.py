import glob
import os
import re
import numpy as np
import pandas as pd
import json

from text_features import clean_text


def ocr_loader(json_path):
    """Helper function to load ocr data from json file

    Args:
        json_path (string):
            Path to the json file with OCR output data

    Returns:
        string:
            OCR text output
    """
    json_path = json_path.replace('\\', '/')
    with open(json_path, "r") as file:
        loaded_json = json.load(file)
        if type(loaded_json) is list:
            result = loaded_json
        else:
            result = loaded_json['text']
        return " ".join(result)


def read_ocr_from_json(df):
    """Creates new column (`OCRText`) and loads OCR text into that column

    Args:
        df (pandas.DataFrame):
            Input DataFrame

    Returns:
        pandas.DataFrame:
            DataFrame with new column holding OCR results
    """
    df['OCRText'] = df['OCRJsonPath'].apply(
        lambda x: ocr_loader(x)
    )
    return df


def create_dataframe_from_csv(
        csv_file,
        data_dir,
        filename_col='FileName',
        load_ground_truth=None,
        dropna=True):
    """
    Create a dataframe with base columns used later for processing.
    This function assumes that the file pattern looks as follows:
    `<FILENAME>.<FILE_EXT>`, so for example OCR results file for `1234567.pdf` would be `1234567.json`  # NOQA E501

    Args:
        csv_file (str):
            Path to CSV file
        data_dir (str):
            Directory for all the files
        filename_col (str, optional):
            Main column with all the PDF filenames.
            Defaults to 'FileName'.
        load_ground_truth (str):
            Path to the CSV file with known labels
        dropna (bool):
            Use to drop rows with NaN values

    Returns:
        pandas.DataFrame:
            Processed DataFrame with all the base required columns
    """
    df = pd.read_csv(csv_file)
    df.fillna('', inplace=True)
    df['FileName'] = df[filename_col].apply(lambda x: x.split('.')[0])
    df['FileName'].astype(str, inplace=True)

    return _create_dataframe(
        df, data_dir,
        load_ground_truth, dropna)


def create_dataframe_from_pd(
        dataframe,
        data_dir,
        filename_col='FileName',
        load_ground_truth=None,
        dropna=True):
    """
    Create a dataframe with base columns used later for processing.
    This function assumes that the file pattern looks as follows:
    `<FILENAME>.<FILE_EXT>`, so for example OCR results file for `1234567.pdf` would be `1234567.json`  # NOQA E501

    Args:
        dataframe (pandas.DataFrame):
            DataFrame with `FileName` column represeting PDF files
        data_dir (str):
            Directory for all the files
        filename_col (str, optional):
            Main column with all the PDF filenames.
        load_ground_truth (str):
            Path to the CSV file with known labels
        dropna (bool):
            Use to drop rows with NaN values

    Returns:
        pandas.DataFrame:
            Processed DataFrame with all the base required columns
    """
    df = dataframe
    df.fillna('', inplace=True)
    df['FileName'] = df[filename_col].apply(lambda x: x.split('.')[0])
    df['FileName'].astype(str, inplace=True)

    return _create_dataframe(
        df, data_dir,
        load_ground_truth, dropna)


def _create_dataframe(
        df, data_dir,
        load_ground_truth,
        dropna):
    """
    Create a dataframe with base columns used later for processing.
    This function assumes that the file pattern looks as follows:
    `<FILENAME>.<FILE_EXT>`, so for example OCR results file for `1234567.pdf` would be `1234567.json`  # NOQA E501

    Args:
        df (pandas.DataFrame):
            Input DataFrame to process
        data_dir (str):
            Directory for all the files
        load_ground_truth (str):
            Path to the CSV file with known labels
        dropna (bool):
            Use to drop rows with NaN values

    Returns:
        pandas.DataFrame:
            Processed DataFrame with all the base required columns
    """
    df['ImagePath'] = df['FileName'].apply(
        lambda x: os.path.join(data_dir, x + '.png'))
    df['ImageName'] = df['ImagePath'].apply(
        lambda x: os.path.basename(x))
    df.set_index('ImageName', inplace=True)
    df.drop_duplicates(inplace=True)
    # if first_page_only:
    #     df = df[df['ImagePath'].str.contains('_0.')]
    df['PDFPath'] = df['FileName'].apply(
        lambda x: os.path.join(data_dir, x + '.pdf'))
    df['OCRJsonPath'] = df['FileName'].apply(
        lambda x: os.path.join(data_dir, x + '.json'))

    df['LayoutType'] = '-1'
    if load_ground_truth:
        df_gt = pd.read_csv(load_ground_truth)
        df_gt.set_index('ImageName', inplace=True)
        df.loc[df_gt.index.values, 'LayoutType'] = df_gt['LayoutType'].values

    if dropna:
        print("Rows count before removing NaN values: ", len(df))
        df.dropna(inplace=True)
        print("Rows count after removing NaN values: ", len(df))
        # df.reset_index(drop=True, inplace=True)

    return df


def create_dataframe_from_files(
        data_dir,
        file_ext='.pdf',
        load_ground_truth=None,
        dropna=True):
    """
    Creates the base dataframe based on specific file extension and data dir.

    Args:
        data_dir (str):
            Directory for all the files
        file_ext (str, optional):
            File extension to use.
            Select from: ['.pdf', '.png', '.jpg', '.json']
            Defaults to '.pdf'.
        load_ground_truth (str):
            Path to the CSV file with known labels
        dropna (bool):
            Use to drop rows with NaN values

    Returns:
        pandas.DataFrame:
            Base dataframe with all the base columns
    """

    extensions = ['.pdf', '.png', '.jpg', '.json']
    assert(file_ext in extensions)

    column_map = dict(zip(
        extensions, ['PDFPath', 'ImagePath', 'ImagePath', 'OCRJsonPath']
    ))

    all_files = glob.glob(os.path.join(data_dir, "*" + file_ext))
    if len(all_files) == 0:
        raise ValueError(
            "Couldn't find any files with extension '%s' under directory: '%s'" % (  # NOQA E501
                file_ext, data_dir))

    df = pd.DataFrame({
        column_map[file_ext]: all_files,
    })

    df['FileName'] = df[column_map[file_ext]].apply(
        lambda x: os.path.basename(x).split('.')[0])  #.split('_')[0]

    return _create_dataframe(
        df, data_dir,
        load_ground_truth, dropna)


def clean_text_column(
        df,
        chars_regex="[a-zA-Z&]+",
        keep='all',
        min_words_count=20,
        remove_empty=True):
    """
    Wrapper that applies text cleaning function
    (text_features.clean_text) over each row of input DataFrame.

    Args:
        df (pandas.DataFrame):
            Input DF with `OCRText` column holding the text to be cleaned
        chars_regex (str, optional):
            Regex to use for characters whitelisting.
            Defaults to "[a-zA-Z&]+".
        keep (str, optional):
            'header' - take top 1/3 of the text
            'header+bottom' - take top 1/3 and bottom 1/3 of the text
            'all' - take all the text
            Defaults to 'all'.
        min_words_count (int, optional):
            Threshold for minimum words present.
            Returns empty string if below threshold.
            Defaults to 20.
        remove_empty (bool, optional):
            Remove empty strings.
            Defaults to True.

    Returns:
        pandas.DataFrame:
            DataFrame with `TextClean` column
    """

    df['TextClean'] = df['OCRText'].apply(
        lambda x: clean_text(
            x, findall=chars_regex,
            keep=keep, min_words_count=min_words_count))

    if remove_empty:
        print('Removing empty texts: ', sum(df['TextClean'] == ''))
        df = df[df['TextClean'] != '']
        print("Total rows count: ", len(df))
        # df.reset_index(drop=True, inplace=True)

    return df
