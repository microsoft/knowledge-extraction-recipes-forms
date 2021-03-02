#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import csv
import json
import os
import pandas as pd
from typing import List, Optional, Dict
from .ColumnNames import ColumnNames

class StructuredDataLoader():
    """
    Class for help accessing structured training data. The data is
    assumed to have the following structure:
    
    top_level_path
    |- layout1 
        |- layout1config.json 
        |- train 
            |- layout1_train.csv 
            |- form11.jpg 
            |- form11.jpg.ocr.json (Computer Vision's OCR cache)
            |- form11.jpg.al.json (Form Recognizer's Analyze Layout cache)
            ... 
        |- test 
            |- layout1_test.csv 
            |- form12.jpg 
            |- form12.jpg.ocr.json
            |- form12.jpg.al.json 
            ... 
        |- validate 
            |- layout1_validate.csv 
            |- form13.jpg 
            |- form13.jpg.ocr.json
            |- form13.jpg.al.json
            ... 
    ... 
    |- outputs # Gets ignored
        |- miscellaneous output files

    For terminology, use the following terminology:
        * layout: A unique instance of a form layout that we train a form recongizer instance for
        * subdataset: Either 'train', 'test' or 'validate'. Allows for separation of data
    
    Typical usage follows:
        ```python
        sdl = StructuredDataLoader(top_level_path, "train")
        data = sdl.load_dataframe()
        configs = sdl.load_form_recognizer_configs()
        ```
    """

    def __init__(self, top_level_path: str, subdataset: str, layouts: Optional[List[str]] = None):
        """Initialization method to determine available data for loading

        :param str top_level_path: local path to where the training data exists
        :param str subdataset: the subdataset to get data for. Must be in ['train', 'test', 'validate']
        :param List[str] layouts: list of layouts to load. If not provided, all available layouts will be loaded
        """
        self.top_level_path = top_level_path
        
        if layouts is not None:
            for layout in layouts:
                if not os.path.isdir(os.path.join(top_level_path, layout)):
                    raise Exception(f"Layout '{layout}' has no matching directory")
            self.layouts = layouts
        else:
            layouts = os.listdir(top_level_path)
            layouts = [f for f in layouts if f != "outputs"] # removes the outputs directory
            self.layouts = layouts
        
        if subdataset.lower() in ['train', 'test', 'validate']:
            self.subdataset = subdataset.lower()
        else:
            raise Exception(f"subdataset value {self.subdataset} is not accepted. Must be one of 'train', 'test', 'validate'")

    def load_dataframe(self) -> pd.DataFrame:
        """Loads a single data frame holding the ground truth for available data
        
        The following columns get appended:
        'qualified_filename' - full path to the form
        'layout' - name of the layout the form belongs to

        :returns: dataframe holding the available data
        """
        data = pd.DataFrame()
        for layout in self.layouts:
            cur_folder = os.path.join(self.top_level_path, layout, self.subdataset)
            cur_data = self._load_folder(cur_folder, layout)
            data = pd.concat([data, cur_data], ignore_index=True)
        
        return data
    
    def load_form_recognizer_configs(self) -> Dict[str, Dict]:
        """Gets all form recognizer configs from the directory structure
        
        Assumption: configs live in the layout's directory with the name '{layout}_config.json'

        :returns: Dictionary with key's equal to layout and value the parsed config
        """
        configs = {}

        for layout in self.layouts:
            config_file_name = os.path.join(self.top_level_path, layout, f"{layout}_config.json")
            
            if not os.path.isfile(config_file_name):
                raise Exception(f"Missing config file for layout '{layout}'")
            
            with open(config_file_name, 'r') as f:
                configs[layout] = json.load(f)

        return configs            

    
    def _load_folder(self, path_to_subdataset: str, layout: str) -> pd.DataFrame:
        """Load CSV as a data frame for a given layout and subdataset.
        
        Verifies that all specified forms exist and throws if they do not
        Adds qualified_filename and layout columns
        
        :param str path_to_subdataset: path to directory containing csv '{self.path}/{layout}/{subdataset}'
        :param str layout: name of the layout to append into the data frame for routing's use
        :returns: Dataframe representation of the csv ground truth file
        """
        all_files = os.listdir(path_to_subdataset)
        csv_file = [f for f in all_files if f.endswith(".csv")]

        if len(csv_file) != 1:
            raise Exception(f"Found {len(csv_file)} csv files in path {path_to_subdataset}")
        
        data = pd.read_csv(
            os.path.join(path_to_subdataset, csv_file[0]),
            quoting=csv.QUOTE_ALL,
            quotechar='"',
            dtype='string'
        )
        
        data[ColumnNames.QUALIFIED_FILENAME] = data.apply(lambda row: os.path.join(path_to_subdataset, row[ColumnNames.FORM_NAME]), axis=1)
        data[ColumnNames.LAYOUT] = layout
        
        # Verify all forms exist
        for _, row in data.iterrows():
            if not os.path.isfile(row[ColumnNames.QUALIFIED_FILENAME]):
                raise Exception(f"Missing file {row[ColumnNames.QUALIFIED_FILENAME]} for layout {layout}")

        return data
