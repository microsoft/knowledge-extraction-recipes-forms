#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import argparse
from datetime import datetime
import logging

from src.AzureComputerVisionReadApi import AzureComputerVisionReadApi
from src.Secrets import Secrets
import src.routing_helpers as rh
from src.RoutingModel import RoutingModel

def main(model, image):
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S")
    log: logging.Logger = logging.getLogger(__name__)
    
    secrets = Secrets.from_env()

    # Load the model
    routing_model = RoutingModel.json_deserialize(model)
    log.info(f"Successfully loaded routing model: {model}")
    log.info(f"Model can route the layouts: {routing_model.layouts}")

    # Get OCR results for image
    ocr_provider = AzureComputerVisionReadApi(secrets.OCR_SUBSCRIPTION_KEY, secrets.OCR_ENDPOINT)
    words = ocr_provider.get_ocr_results(image)
    log.info(f"Successfully called OCR for image: {image}")

    # Make the prediction
    layout, confidence = routing_model.classify_ocr_results(words, include_probability=True)
    log.info(f"Image identified as {layout} with confidence score of {confidence}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train a routing model")
    parser.add_argument("model",
                        help="Path to a trained routing model JSON")
    parser.add_argument("image",
                        help="Path to an image to route")

    args = parser.parse_args()

    main(args.model, args.image)