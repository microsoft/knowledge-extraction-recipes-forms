#!/usr/bin/python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import shutil
from datetime import datetime, timedelta

from PIL import Image, ImageSequence  # type: ignore
from azure.datalake.store import core, lib, multithread
from azure.storage.blob import (
    BlockBlobService,
    ContainerPermissions
)
from dotenv import load_dotenv
from fpdf import FPDF

load_dotenv()


def get_adl_client(adls_account_name, tenant_id):
    """

    :param adls_account_name: Data Lake account
    :param tenant_id: Azure AD Tenant Id
    :return: client object
    """
    adls_credentials = lib.auth(tenant_id=tenant_id, resource='https://datalake.azure.net/')
    adls_fs_client = core.AzureDLFileSystem(adls_credentials, store_name=adls_account_name)

    return adls_fs_client


def extract_multi_page_tiff(image_folder, temp_folder, file_name, image_path, ext="jpg"):
    """
    We convert to multi-page PDF by first converting locally to jpg
    :param image_folder: Folder where TIFs are
    :param temp_folder: Where we convert to JPG
    :param file_name: Active fil name being processed
    :param image_path: Full path to image
    :param ext: File extension
    :return: list of pages and size of image
    """
    input_file_path = image_folder + os.path.sep + file_name
    base_name, _ = os.path.splitext(file_name)

    input_img = Image.open(image_path)
    print(f"num pages: {input_img.n_frames}  size: {input_img.size}")

    pages = []
    for i, page in enumerate(ImageSequence.Iterator(input_img)):
        # save individual image
        output_file_name = f"{base_name}_{i}.{ext}"
        page_output_file_path = temp_folder + os.path.sep + output_file_name
        page.save(page_output_file_path)
        pages.append(output_file_name)

    return pages, input_img.size


def convert_files_to_pdf(vendor_folder_path, ext):
    """
    TODO - Implement if needed
    :param vendor_folder_path:
    :param ext:
    :return:
    """
    # get list of files in the folder
    input_doc_files = [f for f in os.listdir(vendor_folder_path) if f.endswith(ext)]

    for input_doc_file in input_doc_files:
        try:
            image_file_path = vendor_folder_path + '/' + input_doc_file
            base_name, ext = os.path.splitext(input_doc_file)
            image_output_path = f"{vendor_folder_path}/{base_name}.pdf"

            if os.path.exists(image_output_path):
                print(f"already exists so skipping conversion: {image_file_path} --> {image_output_path}")
                continue

            write_to_fpdf(vendor_folder_path, image_output_path, input_doc_file)
        except Exception as e:
            print(e)


def write_to_fpdf(input_folder, output_file_path, image_file):
    """
    Convert to the TIF to PDF
    :param input_folder: Working folder
    :param output_file_path: Where we write to
    :param image_file: The active image file being processed
    :return: Nothing
    """
    pdf = FPDF()
    pdf.set_auto_page_break(0)

    image_file_path = input_folder + os.path.sep + image_file

    cover = Image.open(image_file_path)
    width, height = cover.size

    # convert pixel in mm with 1px=0.264583 mm
    width, height = float(width * 0.264583), float(height * 0.264583)

    # given we are working with A4 format size
    pdf_size = {'P': {'w': 210, 'h': 297}, 'L': {'w': 297, 'h': 210}}

    # get page orientation from image size
    orientation = 'P' if width < height else 'L'

    #  make sure image size is not greater than the pdf format size
    width = width if width < pdf_size[orientation]['w'] else pdf_size[orientation]['w']
    height = height if height < pdf_size[orientation]['h'] else pdf_size[orientation]['h']

    pdf.add_page(orientation=orientation)

    pdf.image(image_file_path, 0, 0, width, height)

    pdf.output(output_file_path, "F")


def write_to_pdf(output_path: str, image: Image):
    """
    TODO - Implement if needed
    :param output_path:
    :param image:
    :return:
    """
    count = 0
    with open(output_path, 'wb+') as output:
        for i, page in enumerate(ImageSequence.Iterator(image)):
            print(f"Processing page {i} of {output_path}")

            antialias = page.resize(page.size, resample=Image.ANTIALIAS)
            rgb_antialias = antialias.convert('RGB')
            count += 1
            rgb_antialias.save(output,
                               format="PDF",
                               append=True,
                               save_all=True,
                               optimize=True,
                               quality=1)

    if count > 1:
        print(f"count: {count}  {output_path}")


class Config:
    """
    Read from .env file
    """
    TRAINING_END_POINT = os.environ.get("TRAINING_END_POINT")  # FR Training endpoint
    ANALYZE_END_POINT = os.environ.get("ANALYZE_END_POINT")  # OCR endpoint
    SUBSCRIPTION_KEY = os.environ.get("SUBSCRIPTION_KEY")  # CogSvc key
    STORAGE_ACCOUNT_NAME = os.environ.get("STORAGE_ACCOUNT_NAME")  # Account name for storage
    STORAGE_KEY = os.environ.get("STORAGE_KEY")  # The key for the storage account
    KEY_FIELD_NAMES = os.environ.get("KEY_FIELD_NAMES")  # The fields to be extracted e.g. invoicenumber,date,total
    ADLS_ACCOUNT_NAME = os.environ.get("ADLS_ACCOUNT_NAME")  # Data lake account
    ADLS_TENANT_ID = os.environ.get("ADLS_TENANT_ID")  # Azure AD tenant id
    SAS_PREFIX = os.environ.get("SAS_PREFIX")  # First part of storage account
    SAS = os.environ.get("SAS")  # SAS for storage
    RUN_FOR_SINGLE_ISSUER = os.environ.get("RUN_FOR_SINGLE_ISSUER")  # If true process only this vendor
    MOUNT_DIR = os.environ.get("MOUNT_DIR")  # Model mount directory to which to write training files to
    DOC_EXT = os.environ.get("DOC_EXT")  # The extension of the files to process e.g. .tif
    LANGUAGE_CODE = os.environ.get("LANGUAGE_CODE")  # The language we invoke Read OCR in only en supported now
    GROUND_TRUTH_PATH = os.environ.get("GROUND_TRUTH_PATH")  # This is the path to our Ground Truth
    LOCAL_WORKING_DIR = os.environ.get(
        "LOCAL_WORKING_DIR")  # The local temporary directory to which we write and remove
    CONTAINER_SUFFIX = os.environ.get(
        "CONTAINER_SUFFIX")  # The suffix name of the containers that store the training datasets
    LIMIT_TRAINING_SET = os.environ.get("LIMIT_TRAINING_SET")  # For testing models by file qty trained on
    ADLS_PATH = os.environ.get("ADLS_PATH")  # Path in ADLS
    TRAIN_TEST = os.environ.get("TRAIN_TEST")  # Suffixes train or test to container name


def create_pdf(input_folder, output_file_path, file_name_list):
    """
    Part of the conversion of TIF to PDF - we used FPDF as this is used by Form Recognizer and
    avoids segfaults we experienced
    :param input_folder: Active input folder
    :param output_file_path: Where we write to
    :param file_name_list: List of files to process
    :return: Nothing
    """
    pdf = FPDF()
    pdf.set_auto_page_break(0)

    for image_file in file_name_list:
        image_file_path = input_folder + os.path.sep + image_file
        print(image_file_path)
        cover = Image.open(image_file_path)
        width, height = cover.size

        # convert pixel in mm with 1px=0.264583 mm
        width, height = float(width * 0.264583), float(height * 0.264583)

        # given we are working with A4 format size
        pdf_size = {'P': {'w': 210, 'h': 297}, 'L': {'w': 297, 'h': 210}}

        # get page orientation from image size
        orientation = 'P' if width < height else 'L'

        #  make sure image size is not greater than the pdf format size
        width = width if width < pdf_size[orientation]['w'] else pdf_size[orientation]['w']
        height = height if height < pdf_size[orientation]['h'] else pdf_size[orientation]['h']

        pdf.add_page(orientation=orientation)

        pdf.image(image_file_path, 0, 0, width, height)

    pdf.output(output_file_path, "F")


def create_container(block_blob_service, account_name, container_name):
    """
    This function creates the container if it does not exist
    :param block_blob_service: The storage blob service instance
    :param account_name: The storage account name
    :param container_name: The storage container
    :return: The SAS for the container
    """
    print('container name', container_name)

    if not block_blob_service.exists(container_name):
        block_blob_service.create_container(container_name)

    sas_qs = block_blob_service.generate_container_shared_access_signature(
        container_name,
        ContainerPermissions.READ | ContainerPermissions.LIST,
        expiry=datetime.now() + timedelta(days=1)
    )

    container_sas_url = f"https://{account_name}.blob.core.windows.net/{container_name}?{sas_qs}"

    return container_sas_url, sas_qs


def upload_blobs_to_container(block_blob_service, input_folder_path, container_name, ext):
    """

    :param block_blob_service: Our blob storage instance
    :param input_folder_path: The folder we are working with
    :param container_name: The blob storage container name
    :param ext: File extension 'pdf'
    :return: Nothing
    """
    print('Upload files', input_folder_path, container_name, ext)
    document_files = [f for f in os.listdir(input_folder_path) if f.endswith(ext)]

    for doc_file_name in document_files:
        doc_file_path = input_folder_path + os.path.sep + doc_file_name
        block_blob_service.create_blob_from_path(
            container_name, doc_file_name, doc_file_path)


def convert_tif_to_pdf_fpdf(image_folder, temp_folder, file_name, vendorname):
    """

    :param image_folder: Active input folder
    :param temp_folder: Where we perform temporary conversions
    :param file_name: Active file name being processed
    :param vendorname: Vendor we are processing
    :return: Nothing
    """
    folder_path = image_folder

    base_name, _ = os.path.splitext(file_name)
    output_file_name = base_name + '.pdf'
    image_path = folder_path + os.path.sep + file_name

    output_file_path = folder_path + os.path.sep + output_file_name

    file_name_list, _ = extract_multi_page_tiff(output_file_path, temp_folder, file_name,
                                                image_path)
    print('Coverted to', output_file_path, file_name)
    create_pdf(folder_path, output_file_path, file_name_list)


def main():
    """
    Entry point
    :return:
    """
    rf = Config.LOCAL_WORKING_DIR

    adl_path = Config.ADLS_PATH

    adl_client = get_adl_client(Config.ADLS_ACCOUNT_NAME, Config.ADLS_TENANT_ID)
    adl_folders = adl_client.ls(adl_path)

    # For training_file in training_files:
    print(adl_folders)

    # Loop through vendors download images and convert to pdf
    for adl_vendor_path in adl_folders:
        print(f"Processing vendor {adl_vendor_path}")

        if len(Config.RUN_FOR_SINGLE_ISSUER) > 0:
            if Config.RUN_FOR_SINGLE_ISSUER not in adl_vendor_path:
                continue

        vendor_folder = os.path.split(adl_vendor_path)[-1]
        vendor_folder_path = f"{rf}/{vendor_folder}"
        if not os.path.exists(vendor_folder_path):
            print(f"Creating folder {vendor_folder_path}")
            os.mkdir(vendor_folder_path)

        # Download all the files for a vendor
        # TODO we are using Azure Data Lake here change to appropriate

        multithread.ADLDownloader(
            adl_client,
            lpath=vendor_folder_path,
            rpath=adl_vendor_path,
            nthreads=64,
            overwrite=True,
            buffersize=4194304,
            blocksize=4194304)

        tif_files = [f for f in os.listdir(vendor_folder_path) if f.endswith('TIF')]

        # Create the BlockBlockService that the system uses to call the Blob service for the storage account.
        block_blob_service = BlockBlobService(
            account_name=Config.STORAGE_ACCOUNT_NAME, account_key=Config.STORAGE_KEY)

        temp_folder = vendor_folder_path
        for file_name in tif_files:

            print(f"Create temp folder {temp_folder}")
            if not os.path.exists(temp_folder):
                os.mkdir(temp_folder)

            try:
                print(f"Processing {vendor_folder}")
                convert_tif_to_pdf_fpdf(vendor_folder_path,
                                        temp_folder,
                                        file_name, vendor_folder)
            except Exception as e:
                print(e)
                continue

        container_name = vendor_folder + Config.CONTAINER_SUFFIX + Config.TRAIN_TEST
        print(f"Uploading to blob {container_name}")

        # Create container if it doesn't exist and get container sas url
        _, _ = create_container(block_blob_service, Config.STORAGE_ACCOUNT_NAME, container_name)

        # Upload to container
        upload_blobs_to_container(block_blob_service, vendor_folder_path, container_name, '.pdf')
        print(f"Removing folder {vendor_folder_path}")
        shutil.rmtree(vendor_folder_path)


if __name__ == "__main__":
    main()
