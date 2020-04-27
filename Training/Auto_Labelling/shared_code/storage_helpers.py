import logging
import hashlib
import base64
import hmac
import datetime
import urllib 

from azure.storage.blob import BlobServiceClient, ContainerClient, PublicAccess
from azure.storage.queue import QueueServiceClient, QueueClient, QueueMessage
from azure.cosmosdb.table.tableservice import TableService
from azure.cosmosdb.table.models import Entity

##############
# BLOB STORAGE
##############

# Creates an Azure Blob Storage service
def create_container_client(account_url, container_name, sas):
    container_client = None
    try:
        container_url = account_url + '/' + container_name + sas
        container_client = ContainerClient.from_container_url(container_url)
        logging.info(f"Created container client for container {container_name} in account {account_url}.")
    except Exception as e:
        logging.error(f"Could not create container client for container {container_name} in account {account_url}: {e}")
    return container_client

# Lists all the pdf blobs in a given folder within a container
def list_blobs(container_client, folder_name, show_all = False, recursive = False):
    blobs = []
    try:
        blob_list = container_client.list_blobs()
        print(blob_list)
        for blob in blob_list:
            path_parts = blob.name.split('/')
            folder = '/'.join(path_parts[i] for i in range(len(path_parts)-1))
            if(blob.size > 0 and ((recursive == False and folder == folder_name) or (recursive == True and folder.startswith(folder_name)))):
                if(show_all): blobs.append(blob.name)
                elif (blob.name.split('.')[-1] == 'pdf'): blobs.append(blob.name)
        logging.info(f"Found {str(len(blobs))} blobs in folder {folder_name}.")
    except Exception as e:
        logging.error(f"Could not list blobs in folder {folder_name}: {e}")
    return blobs

def delete_folder(container_client, folder_name):
    for blob in list_blobs(container_client, folder_name, True, True):
        blob_client = container_client.get_blob_client(blob)
        blob_client.delete_blob()

def blob_name_contains_folder(name):
  return len(name.split('/')) > 1

def get_blob_root_folder(name):
  if(blob_name_contains_folder(name)):
    index = name.find("/")
    return name[:index]
  return None

def copy_folder(container_client, src_folder, dest_folder, recursive = True, recreate_destination = True):
    blobs = list_blobs(container_client, src_folder, True, recursive)
    if(len(blobs) > 0):
        if(recreate_destination == True): delete_folder(container_client, dest_folder)
        for blob in blobs:
            blob_data = download_blob(container_client, blob)
            new_blob_name = blob.replace(src_folder, dest_folder)
            upload_blob(container_client, new_blob_name, blob_data)

# Lists all the folders in a given container
def list_doctype_folders(container_client):
    folders = []
    try:
        blobs = container_client.list_blobs()
        for blob in blobs:
            root_folder = get_blob_root_folder(blob.name)
            if root_folder:
                folders.append(root_folder)
        logging.info(f"Found {str(len(folders))} folders.")
    except Exception as e:
        logging.error(f"Could not list folders: {e}")
    return folders

# Lists all the folders in a given container
def list_folders(container_client):
    folders = []
    try:
        blobs = container_client.list_blobs()
        for blob in blobs:
            if(len(blob.name.split('/')) == 1):
                print(blob.name)
                folders.append(blob.name)
        logging.info(f"Found {str(len(folders))} folders.")
    except Exception as e:
        logging.error(f"Could not list folders: {e}")
    return folders

# Creates a blob in blob storage from local text, file or bytes
def upload_blob(container_client, blob_name, data, upload_type="text"):
    if(upload_type == "text"):
        try:
            container_client.upload_blob(name=blob_name,data=data)
            logging.info("Created blob %s from text successfully."%blob_name)
            return True
        except Exception as e:
            try:
                container_client.delete_blob(blob_name)
                container_client.upload_blob(name=blob_name,data=data)
                logging.info("Created blob %s from text successfully."%blob_name)
                return True
            except Exception as e:
                logging.error("Error creating blob %s from text: %s"%(blob_name,e))
    return False
    
# Gets a blob from blob storage locally as text, bytes or path
def download_blob(container_client, blob_name, download_type='bytes', path=''):
    output = None
    stream = None
    try:
        stream = container_client.download_blob(blob_name)
    except Exception as e:
        logging.error(f"Could not download blob {blob_name}.")
    if stream != None:
        if(download_type == 'text'):
            try:
                output = stream.readall()
                logging.info(f"Retrieved blob {blob_name} as text successfully.")
            except Exception as e:
                logging.error(f"Error retrieving blob {blob_name} as text: {e}")
        elif(download_type == 'bytes'):
            try:
                output = stream.readall()
                logging.info(f"Retrieved blob {blob_name} as bytes successfully.")
            except Exception as e:
                logging.error(f"Error retrieving blob {blob_name} as bytes: {e}")
        elif(download_type == 'path'):
            try:
                with open(path, 'wb') as f:
                    stream.download_to_stream(f)
                output = path
                logging.info(f"Retrieved blob {blob_name} and saved it to local path {path} successfully.")
            except Exception as e:
                logging.error(f"Error retrieving blob {blob_name} and saving it to local path {path}: {e}")
        else:
            logging.error("Please provide a valid download type (text, bytes or path).")
    return output        
       

###############
# TABLE STORAGE
###############

# Creates an Azure Table Storage service
def create_table_service(account_name, account_key):
    table_service = None
    try:
        table_service = TableService(account_name=account_name, account_key=account_key)
    except Exception as e:
        logging.error("Could not instantiate table service: %s"%e)
    return table_service
    
# Creates an entity if it doesn't exist, updates it if it does
def insert_or_replace_entity(table_service, table_name, entity):
    try:
        table_service.insert_or_replace_entity(table_name, entity)
        return True
    except Exception as e:
        logging.error("Could not insert or update entity in table %s:%s"%(table_name,e))
        return False

# Queries a table to get an entity's status, returns None if the entity doesn't exist
def query_entity_status(table_service, table_name, partition_key, row_key):
    try:
        entity = table_service.get_entity(table_name, partition_key, row_key)
        status = entity.status
        return status
    except Exception as e:
        logging.info("Could not query entity %s in table %s:%s"%(row_key,table_name,e))
        return None

def query_entity_model(table_service, table_name, partition_key, row_key):
    try:
        entity = table_service.get_entity(table_name, partition_key, row_key)
        model_id = entity.modelId
        return model_id
    except Exception as e:
        logging.info("Could not query entity %s in table %s:%s"%(row_key,table_name,e))
        return None

# Queries a table to get a list of entities
def query_entities(table_service, table_name, partition_key):
    try:
        entities = table_service.query_entities(table_name, filter=f"PartitionKey eq '{partition_key}'")
        logging.info(f"Retrieved entities with partition key {partition_key}.")
        return [e.status for e in entities]
    except Exception as e:
        logging.error(f"Could not query entities with partition key {partition_key}: {e}")
        return None


##############
# Queue STORAGE
##############

# Creates an Azure Blob Storage service
def create_queue_client(account_name, account_key, queue_name):
    queue_client = None
    try:
        connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
        queue_client = QueueClient.from_connection_string(connection_string, queue_name)
        logging.info(f"Created queue client for queue {queue_name} in account {account_name}.")
    except Exception as e:
        logging.error(f"Could not create queue client for queue {queue_name} in account {account_name}: {e}")
    return queue_client

def get_queue_message(queue_client):
    try:
        messages = queue_client.receive_messages()
        for message in messages:
            return message
    except Exception as e:
        logging.error(f"Could not retrieve queue messages: {e}")
        return None

def delete_queue_message(queue_client, message):
    try:
        queue_client.delete_message(message)
        return True
    except Exception as e:
        logging.error(f"Could not delete message from queue: {e}")
        return False

def add_queue_message(queue_client, message_str):
    msg = None
    try:
        msg = queue_client.send_message(message_str)
    except Exception as e:
        logging.error(f"Could not add message to queue: {e}")
    return msg

def get_queue_message_str(queue_client):
    message = get_queue_message(queue_client)
    if(message is None):
        return None
    else:
        msg = message.content
        queue_client.delete_message(message)
    return msg