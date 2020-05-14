# The AutoLabelling process

This document describes how to implement the autolabelling process for the Supervised version of Forms Recognizer. By using an autolabelling approach we are able to reduce but not remove the need for a *human-in-the-loop*. It is strongly recommended that manual labelling still takes place for poorly performing models, but the need for manual labelling should be significantly reduced.

Note, no specialist skills are required for labelling, and thus with a little training and a disciplined and rigourous approach, poorly perfoming models due to autolabelling failures can be quickly rectified.What we have seen from real project implementations is that Auto-Labelling will produce high accuracy for most of the layout types/models, the poorly performing models will typically be due to mixed layouts, poor quality scans and noise such as messy handwriting overlapping over other text.

To amend the labels or indeed add new ones, or correct an Auto-labelled model please refer to the [Form Recognizer Sample Labelling Tool](https://docs.microsoft.com/en-us/azure/cognitive-services/form-recognizer/quickstarts/label-tool)

The result is that we can obtain the high accuracy scores of a supervised approach but also benefit from the ability to automate training at scale that is typically available in an unsupervised approach.

Note, in order to implement autolabelling, sufficient Ground Truth (GT) data must be available. The autolabelling process is very much a data driven process, and thus the more data available, and the more representative it is of the final production data, the better the end results and accuracy.

The image below illustrates the overall process:

<img src="../../Project_Preparation/Decision_Guidance/repo_images/AutoLabelTrain.png" align="center" alt="" width="500"/>

* Step 1 - We retrieve the corresponding GT data for the relevant form
* Step 2 - We perform a double pass of the data and generate two candidate training sets and automatically select the best one
* Step 3 - We train Form Recognizer with the ```Use Labels``` option on the best training dataset
* Step 4 - We check the estimated accuracy of the model on the training data set
* Step 5 - The estimated accuracy score is high, we can proceed to evaluation
* Step 6 - The estimated accuracy score is low, we need to take further action
* Step 7 - We manually correct the erroneous labels to ensure high accuracy
* Step 8 - We collect more GT data and forms in order to improve our dataset and re-run the autolabelling process to see if the accuracy improves

## Logical summary of autolabel_training.py

In summary, the autolabelling process will implement the following steps:

* Prepare the files by converting them from TIF --> JPG --> PDF
* Create Storage Containers with a specific naming convention and uploaded the converted files
* Iterate through every container
* Load the corresponding ground truth record (GT) for an invoice
* Retrieve the values from the GT for the keys we want to extract/tag/label
* Call Read Layout (OCR) for the invoice if no OCR file exists for the invoice
* Search through both the line and word level of the OCR file with formatting to find the ground truth values for the
keys to be extracted.
* If a value is found, get the corresponding page, height, width and bounding box attributes for the original
unformatted OCR value
* Generate the corresponding ocr.labels.json for the invoice
* Upload the label and json files to the Storage Container and train the Supervised version of Forms Recognizer.

The following section describes the various scripts and the sequence they need to be invoked in alongside the
corresponding parameters.

## Prerequisites

The autolabel files require an environment variable file to be created with the name ```.env```

The following environment variables need to be created in this file:

```bash
ADLS_ACCOUNT_NAME=    # Data lake account]
TRAINING_END_POINT=   # FR Training endpoint]
ANALYZE_END_POINT=    # OCR endpoint]
SUBSCRIPTION_KEY=     # CogSvc key]
STORAGE_KEY=          # The key for the storage account]
STORAGE_ACCOUNT_NAME= # Account name for storage]
KEY_FIELD_NAMES=InvoiceNumber,InvoiceDate,NetValue,TaxValue,TotalAmount  
# These are the fields we want to extract
ADLS_TENANT_ID=       # Azure AD tenant id]
SAS=                  # SAS for storage]
SAS_PREFIX=           # First part of storage account e .g. https://myaccountname.blob.core.windows.net/]
MODEL_ID=             # Run for a single model]
TRAIN_TEST=           # Suffixes train or test to container name e.g. train/test]
ADLS_PATH=            # Path in ADLS] ]
RUN_FOR_SINGLE_ISSUER=          # If set process only this vendor id]
UNSUPERVISED_ANALYZE_END_POINT= # Endpoint unsupervised]
USE_UNSUPERVISED=     # Run in unsupervised mode]
SYNONYM_FILE=         # Taxonomy file]
DOC_EXT=              # Extension for documents to process e.g. pdf]
LANGUAGE_CODE=        # The language we invoke Read OCR in only En supported now]
GROUND_TRUTH_PATH=    # This is the path to our Ground Truth]
CONTAINER_SUFFIX=     # The suffix name of the containers that store the training datasets]
LOCAL_WORKING_DIR=    # The local temporary directory to which we write and remove]
LIMIT_TRAINING_SET=   # For testing models by file qty trained on]
COUNTRY_CODE=         # The country code if needed
MODEL_LOOKUP=         # Vendor to modelId lookup file]

```

The following section describes the scripts and the sequence below is the sequence they need to be run in.

## Conversion

Have a look at the accelerator [Prepare files for AutoLabelling](autolabel_prepare_files.py) which contains a few sample functions for format conversion.

Here are a few useful links as well:

* [PDF Miner](https://github.com/pdfminer/pdfminer.six)
* [PDF Focus](https://sautinsoft.com/products/pdf-focus/)
* [ImageMagick](https://imagemagick.org/index.php)

## autolabel_prepare_files.py

This script will:

* Download all folders and files from a datastore, in this example from Azure Data Lake represented by ENV VAR ```ADLS_PATH```. If the ENV VAR ```RUN_FOR_SINGLE_ISSUER``` is set, only this vendor will be processed.

* Convert the files from TIF --> JPG --> PDF
* Create a Storage Container per vendor with name format [vendor] + ENV VAR ```CONTAINER_SUFFIX``` +
ENV VAR ```TRAIN_TEST```

Have a look at the accelerator [Prepare files for AutoLabelling](autolabel_prepare_files.py) for sample code to prepare the training data sets for autolabelling.

## autolabel_training.py

In summary, this script retrieves the ground truth values for the invoices of a vendor and tries to find the values
within the OCR of the invoice. It will invoke the OCR process if no corresponding OCR file exists. It searches the OCR
at both the line (sentence) and word level for a match, after applying formatting.

If the value is found, the Bounding Box coordinates are returned and used to extract the polygon values used by the
VOTT tool to label the forms, which in turn is passed to the Supervised version of Form Recognizer to train the
labels/tags to generate a model. The outcome of this process is to generate two files, namely
'[file name]_labels.json'.

As stated, two passes are made over the invoices, with two temporary folders created to store the download invoice
files, the OCR files and the generated label.json file for the corresponding pass. The script will then determine
which pass yielded:

* The most well labelled files
* The most key fields extracted - Note this is specified by the ENV VAR ```KEY_FIELD_NAMES```
*E.g InvoiceNumber,InvoiceDate*

The following logic is then implemented to select the

This script will:

* Determine which pass yielded the most key fields extracted and if the number of fully labelled files exceeds the
minimum training amount of Forms Recognizer, select that as the training set
* If no pass yields enough fully labelled files, selected the training set with the most key fields extracted, even if
the files are only partially labelled.

These files will then be uploaded to a Storage Container and will be used by Forms Recognizer to train the model.

* Iterate through every container if the name of the container contains ENV VAR ```CONTAINER_SUFFIX``` +
ENV VAR ```TRAIN_TEST``` . Furthermore, the first character of the vendors must start with the value specified by
ENV VAR ```COUNTRY_VENDOR_PREFIX```.  If the ENV VAR ```RUN_FOR_SINGLE_ISSUER``` is set, only this vendor will be
processed.
* Load the corresponding ground truth record (GT) for an invoice. GT file is specified by the ENV VAR
 ```GROUND_TRUTH_PATH```
* Download the files to a local directory specified by the ENV VAR ```LOCAL_WORKING_DIR```
* Retrieve the values from the GT for the keys we want to extract/tag/label. The keys to be extracted are specified by
the ENV VAR ```KEY_FIELD_NAMES```
* Call Read Layout (OCR) for the invoice if no OCR file exists for the invoice. The endpoint for the OCR is specified
 by the ENV VAR ```ANALYZE_END_POINT``` with the Cognitive Subscription endpoint specified by the ENV VAR
 ```SUBSCRIPTION_KEY```
* Search through both the line and word level of the OCR file with formatting to find the ground truth values for the
keys to be extracted.
* If a value is found, get the corresponding page, height, width and bounding box attributes for the original
unformatted OCR value
* Generate the corresponding ocr.labels.json for the invoice
* Upload the label and json files to the Storage Container and train the Supervised version of Forms Recognizer.
The endpoint for Forms Recognizer is specified by the ENV VAR ```TRAINING_END_POINT```. The SAS URL needs to be
passed to Forms Recognizer for training, and this is built from the following ENV VAR, ```SAS_PREFIX``` this is
the first part of the SAS URL which designates the Storage e.g. <https://[myaccountname].blob.core.windows.net/>
and the Storage Container name determined at runtime and the ENV VAR ```SAS```. Note, if using containers that are
running over HTTP, not HTTPS, ensure to select both protocols when generating the SAS

* Lastly all temporary folders will be cleaned and comma separated lookup files will be generated, one per vendor/issuer
and one for the entire batch, with the following columns:
```IssuerId,modelId,fieldNumber,accuracy,numFiles,numFilesInGroundTruth```

The batch file name generated will be composed of the following ENV VARS ```LOCAL_WORKING_DIR```
and ```CONTAINER_SUFFIX``` while the vendor specific file will be composed of [vendorid] + ENV VARS
```LOCAL_WORKING_DIR``` and ```CONTAINER_SUFFIX```

Have a look at the accelerator [AutoLabel Training](autolabel_training.py) for sample code for autolabelling and generating the best training dataset.

Back to the [Training section](../README.md)
