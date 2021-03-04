#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

class ColumnNames:
    """Holds the string names of all columns in the csv training data"""

    # Name of the form, this does not contain any paths
    FORM_NAME = "form_name"

    # Path to the form that can be used for accessing
    QUALIFIED_FILENAME = "qualified_filename"

    # Name of layout folder form was loaded from
    LAYOUT = "layout"