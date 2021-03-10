#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import List, Dict, Any, Optional, Tuple, Union

import sys
import os
import io
import json
import numpy as np
import logging
import pandas as pd
from collections import Counter
from sklearn.decomposition import PCA
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.cluster import DBSCAN, KMeans

sys.path.append("../../")
from Routing_Forms.src.WordAndLayoutEncoder import WordAndLayoutEncoder

class ClusteringModel:
    """
    ClusteringModel encapsulates all the components needed to encode a list of images
    according to the extracted words and the layout of words, and use these as features
    for an unsupervised clustering using DBSCAN. Other clustering methods may be more
    suitable for your dataset, e.g. k-means or agglomerative clustering or HDBSCAN.

    This model primarily interacts with the data via a Pandas Dataframe that contains
    location of the image files. This assumes that the OCR results have been fetched, 
    and stored in the same directory according to the <image_name.jpg>.json convention.
    """

    def __init__(
            self,
            layout_shape: (int, int),
            vocabulary_size: int,
            ocr_provider: object, 
            n_pca_components: int = 200,
            vocabulary: List[str] = None,
            stopwords: List[str] = None,
            pipeline: Pipeline = None
    ):
        """
        Constructor for a clustering model

        :param layout_shape: The dimensions for the layout encoding. (50, 79) works well for credit cards sized images.
        :param vocabulary_size: The size of the vocabulary for the word encoding. 2000-3000 works well for a large number of unrecognized cards.
        :param ocr_provider: An instance of an OCR provider class used to get the words from the image
        :param n_pca_components: The number of desired components for PCA on the word encoding 
        and the layout encoding. The actual number of components is limited by the number of rows of data.
        :param vocabulary: A pre-defined vocabulary if available
        :param stopwords: A list of stopwords to filter out if the vocabulary is regenerated
        :param pipeline: An sklearn pipeline containing the PCAs for the word and layout encoding
        """
        self.layout_shape = layout_shape
        self.vocabulary_size = vocabulary_size
        self.ocr_provider = ocr_provider
        self.n_pca_components = n_pca_components
        self.stopwords = stopwords
        if vocabulary is not None:
            self.encoder = WordAndLayoutEncoder(vocabulary, layout_shape)
        else:
            self.encoder = None
        self.pipeline = pipeline

    def _generate_vocabulary(
            self,
            data: pd.DataFrame,
            image_name_column: str):
        """
        Adapted from plan_agnostic_vocabulary_vector in RoutingClassifier.ipynb

        :param data: Pandas DataFrame containing all the images to be clustered
        :param image_name_column: Column in the dataframe with the filename
        :returns: a list containing the most frequent words in the OCR text for these images
        """

        logging.info(f"Counting extracted words across all images to generate the encoding vocabulary")

        # Finds the most popular words out of a bag comprised of all plans
        # Guarantees a length based on vocabulary_size
        count = 0
        counter = Counter()

        for index, row in data.iterrows():
            try:
                filename = data.loc[index, image_name_column]

                ocr_results = self.ocr_provider.get_ocr_results(filename)

                for word in ocr_results:
                    if not self.stopwords or (word.text.lower() not in self.stopwords):
                        counter.update({word.text: 1})

                count += 1
                if count % 5000 == 0:
                    logging.info(f"Processed {count} images for vocabulary generation")
            except:
                logging.error("Could not locate image file: {}".format(row[image_name_column]))
                raise

        # Create the vocabulary vector based on the most common words
        vocabulary_vector = []
        for word in counter.most_common(self.vocabulary_size):
            vocabulary_vector.append(word[0])

        return vocabulary_vector

    def _encode_dataset(
            self,
            data: pd.DataFrame,
            image_name_column: str):
        """
        Encode all the images designated in the data DataFrame into the word+layout encoding
        by running OCR API (with local caching via the ocr_results utility function)

        :param data: a pandas DataFrame containing a list of images and their metadata
        :param image_name_column: column in the dataframe that has the file paths in the blob storage container
        :returns: a 2D numpy array and an array mask.
        The 2D numpy arrays contains the concatenated word and layout encoding for each encoded image.
        The mask is an array of the same length as the original data.
        A zero entry denotes unsuccessfully encoded image. A one denotes a successfully image
        """

        empty_ocr_count = 0
        mask = np.zeros(len(data))
        encoded_data = np.zeros((len(data), self.vocabulary_size + self.layout_shape[0] * self.layout_shape[1]))

        counter = 0
        for index, row in data.iterrows():
            try:
                filename = data.loc[index, image_name_column]
                ocr_results = self.ocr_provider.get_ocr_results(filename)

                if len(ocr_results) == 0:
                    empty_ocr_count += 1
                else:
                    mask[counter] = 1
                    encodings = self.encoder.encode_ocr_results(ocr_results)
                    encoded_data[counter, :] = encodings

            except:
                logging.error("Could not locate blob: {}".format(row[image_name_column]))
                raise

            counter += 1

        if empty_ocr_count > 0:
            logging.warning("Empty OCR results resulting in null entries for {} images".format(empty_ocr_count))

        return encoded_data, mask


    def find_clusters(
            self,
            data: pd.DataFrame,
            image_name_column: str,
            min_samples: int = 10,
            epsilon: float = 3):
        """
        Encode the dataset and perform clustering via the following steps:
        1) constructing a vocabulary if it is not already supplied, 
        2) encode the images based on the presence of the vocabulary words and the bounding boxes 
        of the detected text on the image grid. This is accomplished via the `WordAndLayoutEncoder` 
        available in the `Routing_Forms` example.
        3) apply PCA to each encoding component independently then run clustering on the dataset

        The final number of components from applying PCA is determined by the min of the specified
        `n_pca_components` and the size of the data. The resulting encoding is expected to be 
        an array of size 2 * number of components.

        :param data: a Pandas Dataframe containing the image metadata / filename
        :param image_name_column: the column name in the dataframe with the filename
        :param min_samples: DBSCAN parameter controlling the number of samples 
        in a neighborhood for a point to be considered as a core point.
        :param epislon: DBSCAN parameter controlling the maximum distance between two samples 
        for one to be considered as in the neighborhood of the other.        
        :returns: a copy of the data with the "cluster" column added or overwritten, 
        a dataframe containing the encoding with PCA applied (for further data visualization, for example), 
        and the vocabulary used for the word encoding

        """

        # Produce word and layout encoding from the images; there may be empty rows due to failed OCR on an image
        if self.encoder is None:
            vocabulary = self._generate_vocabulary(data, image_name_column)
            self.encoder = WordAndLayoutEncoder(vocabulary, self.layout_shape)

        (encoding, mask) = self._encode_dataset(data, image_name_column)

        if sum(mask) == data.shape[0]:
            logging.info(f"All {sum(mask)} images are successfully encoded")
        else:
            logging.error(f"{data.shape[0] - sum(mask)} images failed encoding")

        # Remove the empty rows before applying PCA
        encoding = encoding[mask == 1, :]
        self.n_pca_components = min(self.n_pca_components, encoding.shape[0])

        transformer = ColumnTransformer(
        [("word_pca", PCA(n_components=self.n_pca_components), list(range(0, self.vocabulary_size)) ),
         ("layout_pca", PCA(n_components=self.n_pca_components), list(range(self.vocabulary_size, self.vocabulary_size + self.layout_shape[0] * self.layout_shape[1])))])
        dbscan = DBSCAN(eps=epsilon, min_samples=min_samples, metric="euclidean", leaf_size=40)

        self.pipeline = Pipeline([("pca", transformer), ("dbscan", dbscan)])
        Y = self.pipeline.fit_predict(encoding)

        data_copy = data.copy()
        data_copy.drop(["cluster"], axis=1, errors="ignore")
        data_copy.loc[mask == 1, "cluster"] = Y

        # A bit of extra work to return the encodings with PCA applied to help with data visualization
        encoded_data = pd.DataFrame(self.pipeline["pca"].transform(encoding))

        return (data_copy, encoded_data, vocabulary)
