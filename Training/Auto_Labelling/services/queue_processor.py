#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .base_processor import BaseProcessor

try:
    from shared_code import storage_helpers
except ModuleNotFoundError:
    from ..shared_code import storage_helpers

class QueueProcessor(BaseProcessor):
    def __init__(self):
        super(QueueProcessor, self).__init__()
       
    def set(self, messages):
        for message in messages:
            storage_helpers.add_queue_message(self.queue_client, message)

    def get_queue_client(self):
        return self.queue_client
    
    def get_queue_message_str(self):
        return storage_helpers.get_queue_message_str(self.queue_client)            