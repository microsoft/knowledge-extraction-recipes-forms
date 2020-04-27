import logging
from .base_processor import BaseProcessor
try:
    from shared_code import storage_helpers
except ModuleNotFoundError:
    from ..shared_code import storage_helpers

class TriggerProcessor(BaseProcessor):
    def __init__(self):
        super(TriggerProcessor, self).__init__()
     
    def list_doctype_folders(self):
        return storage_helpers.list_doctype_folders(self.container_client)

    def run(self,doctype, status, msg, skip_folder_validation = False):
        if(skip_folder_validation == False):
            folders = self.list_doctype_folders()
            if not doctype in folders:
                raise EnvironmentError( f"{doctype} folder was not found in storage.")

        logging.info(f"Found {doctype} folder in storage.")
    
        blobs = self.get_blobs_by(doctype,self.container_client)
        if any(blobs):
            self.process_blobs(blobs, status, self.table_service, msg)
        else:        
            raise NameError(f"Didn't find any training files in storage for {doctype}")
        
    def process_blobs(self, blobs, status, table_service, queue):
        logging.info(f"Adding files to processing queue...")
        messages = []
        for blob in blobs:
            # Add message to queue
            messages.append(blob)
            # Add file status in the status table
            doctype = blob.split('/')[0]
            file_name = blob.split('/')[-1]
            # If the status value is "keep", we keep the current status
            if(status == 'keep'):
                file_status = storage_helpers.query_entity_status(table_service, self.app_settings.status_table, doctype, file_name)
                if file_status == None:
                    file_status = 'new'
            else:
                file_status = status
            entity = {'PartitionKey': doctype, 'RowKey': file_name, 'status': file_status}
            if storage_helpers.insert_or_replace_entity(table_service, self.app_settings.status_table, entity):
                logging.info(f"Updated {blob} status in status table.")
            else:
                logging.error(f"Could not update {blob} status in status table.")
        if queue:
          try:
              queue.set(messages)
              logging.info(f"Put {str(len(messages))} messages in processing queue.")
          except Exception as e:
              logging.error(f"Error putting messages in processing queue: {e}")        

    def get_blobs_by(self,doctype, container_client):
        training_path = doctype + '/train'
        blobs = storage_helpers.list_blobs(container_client, training_path) 
        return blobs

