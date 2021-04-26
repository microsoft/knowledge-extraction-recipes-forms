# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Contains utils for timestamps processing for Custom Vision
"""
from typing import List
import pandas as pd


def get_intervals(df: pd.DataFrame, tolerance: int = 1) -> List[int]:
    """Builds continuous sequences based on the `timestamps` column.
    Uses tolerance to determine the number of neighbors we tolerate when building sequence

    Example 1:
    Input: 1, 2, 3, 5, 8
    Tolerance: 0
    Detected sequences: [1], [2], [3], [5], [8]

    Example 2:
    Input: 1, 2, 3, 5, 8
    Tolerance: 1
    Detected sequences: [1, 2, 3], [5], [8]

    Example 3:
    Input: 1, 2, 3, 5, 8
    Tolerance: 2
    Detected sequences: [1, 2, 3, 5], [8]

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame, containing `timestamp` column
    tolerance : int, optional
        Number of neighbors we tolerate when building sequence, by default 1

    Returns
    -------
    List[int]
        List of timestamps for each row, containing first element of the detected row's sequence
    """
    df = df.sort_values("timestamp")
    timestamps = df.timestamp.values
    first = timestamps[0]
    first_in_seq = [first]
    for i in range(1, len(timestamps)):
        if timestamps[i] - tolerance > timestamps[i - 1]:
            first = timestamps[i]
        first_in_seq.append(first)
    return first_in_seq
