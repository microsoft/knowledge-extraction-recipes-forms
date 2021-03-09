#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import argparse
from datetime import datetime
import imghdr
import logging
import sys
import os

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from src.Secrets import Secrets
import src.routing_helpers as rh
from src.WordAndLayoutEncoder import WordAndLayoutEncoder
from src.RoutingModel import RoutingModel
from src.AzureComputerVisionOcrApi import AzureComputerVisionOcrApi

def main(data_dir, model_name, number_of_words, shape):
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S")
    log: logging.Logger = logging.getLogger(__name__)
    
    secrets = Secrets.from_env()

    # Load the training data from data_dir
    layouts = os.listdir(data_dir)
    layouts = [l for l in layouts if os.path.isdir(os.path.join(data_dir, l))]
    log.info(f"Identified {len(layouts)} layouts: {layouts}")

    file_names = []
    classification_targets = []
    for layout in layouts:
        layout_dir = os.path.join(data_dir, layout)
        images = os.listdir(layout_dir)
        images = [i for i in images if imghdr.what(os.path.join(layout_dir,i))]
        for image in images:
            file_names.append(os.path.join(layout_dir, image))
            classification_targets.append(layout)

        log.info(f"Found {len(images)} images for the layout {layout}")

    # Initialize our OCR provider
    ocr_provider = AzureComputerVisionOcrApi(secrets.OCR_SUBSCRIPTION_KEY, secrets.OCR_ENDPOINT)
    # Load the OCR Api response for each image
    log.info("Begin loading the OCR results...")
    ocr_results = rh.load_data(file_names, ocr_provider)
    log.info("Successfully loaded the OCR results")

    # Generate the vocabulary vector
    log.info("Generating the vocabulary vector...")
    vocabulary_vector = rh.layout_aware_vocabulary_vector(ocr_results, number_of_words, classification_targets)
    log.info(f"Vocabulary of {len(vocabulary_vector)} words created")

    # Encode the data
    routing_encoder = WordAndLayoutEncoder(vocabulary_vector, shape)
    num_features = len(vocabulary_vector) + shape[0] * shape[1]

    # Initializes arrays to receive the encoded results
    X = np.zeros((len(ocr_results), num_features))
    y = []

    log.info("Begin the encoding...")
    for counter, (result, target) in enumerate(zip(ocr_results, classification_targets)):
        X[counter, :] = routing_encoder.encode_ocr_results(result)
        y.append(target)
    log.info("Finished encoding")

    # Create the SKLearn Pipeline
    # Column Transformer will pass through the vocabulary encoding with no 
    # further operations, but train a PCA model for the location information
    ct = ColumnTransformer(
        [("layout", PCA(), slice(len(vocabulary_vector), num_features))],
        remainder="passthrough")

    # Start with the column transformer, then classifier
    estimators = [('ct', ct), ('classifier', RandomForestClassifier(random_state=42))]
    pipe = Pipeline(estimators)

    # Split into train and test steps as a way to see what is going on
    log.info("Train/test split for an idea of how the model performs")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.5, random_state=42, stratify=y)
    log.info("Training model on the train split")
    pipe.fit(X_train, y_train)

    # confusion matrix with labels
    log.info("Predicting on the test split")
    y_test_pred = pipe.predict(X_test)
    log.info(f"Confusion matrix for the test set, with labels: {sorted(layouts)} ")
    print(confusion_matrix(y_test, y_test_pred))
    

    # Fit the final model with the whole dataset (training + test)
    log.info("Training the model on the full dataset")
    pipe.fit(X, y)

    model_path = f"{model_name}.json"

    # Save the model
    tags = {
        "creation_time": str(datetime.utcnow())
    }
    my_model = RoutingModel(vocabulary_vector, shape, tags, layouts, pipe)
    my_model.json_serialize(model_path)
    log.info(f"Saved the model as: {model_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train a routing model")
    parser.add_argument("data_dir",
                        help="Path to directory containing training data")
    parser.add_argument("model_name",
                        help="Name to save the model as")
    parser.add_argument("--number-of-words",
                        default=50,
                        type=int,
                        help="Number of words for the vocabulary vector")
    parser.add_argument("--shape",
                        default=(50, 50),
                        type=int,
                        help="Tuple denoting the dimension of the form layout, e.g. 50 50",
                        nargs=2)
    args = parser.parse_args()

    main(args.data_dir, args.model_name, args.number_of_words, args.shape)
