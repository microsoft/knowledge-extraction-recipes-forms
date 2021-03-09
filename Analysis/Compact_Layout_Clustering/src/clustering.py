#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import argparse
import logging
import sys
import os
import pandas as pd
import numpy as np
from ClusteringModel import ClusteringModel

sys.path.append("../../")
from Routing_Forms.src.Secrets import Secrets
import Routing_Forms.src.routing_helpers as rh

# Additional constants for the clustering pipeline that should be adjusted for your dataset:

# number of PCA components to use
N_PCA_COMPONENTS = 3

# minimum size of a cluster in DBSCAN
MIN_SAMPLES = 5

# maximum distance between two points for them to be included in the same cluster in DBSCAN
EPSILON = 10

def main(env_file, data_dir, layout_shape, vocabulary_size, stopwords_file = None):

    """
    Simple illustration of how to instantiate a ClusteringModel and use it on a collection of images
    """

    # Load secrets for the Azure OCR services from the env file
    secrets = Secrets.from_env(env_file)

    # Read stopwords from the file if given (for excluding words from the encoding vocabulary)
    if stopwords_file is not None:
        with open(stopwords_file, "r") as f:
            stopwords = f.readlines()
    stopwords = [s.strip() for s in stopwords]

    # Grep all the JPG images in the data directory and store the file references in a Pandas DataFrame
    images = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".jpg")]
    for i in images:
        rh.get_ocr_results(i, secrets.OCR_SUBSCRIPTION_KEY, secrets.OCR_ENDPOINT)

    image_data = pd.DataFrame(images, columns=["filename"])

    # Instantiate a Clustering model with the supplied parameters
    cm = ClusteringModel(layout_shape, vocabulary_size, n_pca_components=N_PCA_COMPONENTS, stopwords=stopwords)

    # Run Clustering on the image data
    (clustered_data, encoding, vocabulary) = cm.find_clusters(image_data, "filename", min_samples=MIN_SAMPLES, epsilon=EPSILON)

    # Printing out the output. These can be written out to file as well.
    pd.set_option("display.max_colwidth", 200)
    print(vocabulary)
    print(encoding)
    print(clustered_data.sort_values(by="cluster"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cluster images by layouts")
    parser.add_argument("--env_file", help="Environment variables file")
    parser.add_argument("--data_dir", help="Path to directory with images")
    parser.add_argument("--layout_shape", type=int, help="Tuple denoting the dimension of the form layout, e.g. 50 79", nargs=2)
    parser.add_argument("--vocabulary_size", type=int, help="Size of the vocabulary to use for word encoding, e.g. 100")
    parser.add_argument("--stopwords_file", help="An optional stopwords file for words to exclude from encoding vocabulary", default=None)

    args = parser.parse_args()
    main(args.env_file, args.data_dir, tuple(args.layout_shape), args.vocabulary_size, args.stopwords_file)
