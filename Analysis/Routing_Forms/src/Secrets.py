#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations
import os
from typing import Dict
from urllib.parse import urlparse
from dotenv import load_dotenv


class Secrets():
    """Helper for loading and storing secrets

    If running using the from_env method, it supports secrets
    being passed through a .env file in the same directory
    """

    def __init__(
        self,
        ocr_endpoint: str,
        ocr_subscription_key: str
    ):
        self.OCR_ENDPOINT = ocr_endpoint
        self.OCR_SUBSCRIPTION_KEY = ocr_subscription_key

        self._format_urls()

    def _format_urls(self):
        """Ensures all urls begin with https:// and has no trailing slash"""
        self.OCR_ENDPOINT = self._format_url(self.OCR_ENDPOINT)

    def _format_url(self, input_url: str):
        """Ensures a url value begins with https:// and has no trailing slash
        
        :param str input_url: url to be formatted
        """
        if not input_url.startswith("https://"):
            url_parts = urlparse(input_url)
            url_parts = url_parts._replace(scheme="https")
            if not url_parts.netloc and url_parts.path:  # For case where url is provided with no scheme: i.e. example.com
                url_parts = url_parts._replace(netloc=url_parts.path)
                url_parts = url_parts._replace(path="")
            input_url = url_parts.geturl()

        if input_url.endswith("/"):
            input_url = input_url[:-1]

        return input_url

    @staticmethod
    def from_env(env_file_path=None) -> Secrets:
        """Loads secret variables from environment
        
        By default a `.env` file in the same directory as this file
        will be loaded to provided the environment values. The .env file
        to load can be chosen through the env_file_path parameter.

        :param str env_file_path: if provided, the given .env file will be used
        :return Secret: An instance of secrets, initailized from the env file
        """
        if env_file_path is None:
            load_dotenv()
        else:
            load_dotenv(env_file_path)

        OCR_ENDPOINT = os.getenv("OCR_ENDPOINT")
        OCR_SUBSCRIPTION_KEY = os.getenv("OCR_SUBSCRIPTION_KEY")

        return Secrets(OCR_ENDPOINT, OCR_SUBSCRIPTION_KEY)
