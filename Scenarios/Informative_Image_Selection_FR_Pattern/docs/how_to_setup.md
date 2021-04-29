# How to setup #

This document will give an overview as to how to setup the codebase on a local machine so that the notebooks can be run.

There are four basic steps required to run experiments successfully on your local machine:

- Step 1: Upload dataset to a blob storage container
- Step 2: Set up an Azure Machine Learning Workspace
- Step 3: Create an Azure Form Recognizer and Azure Computer Vision subscription
- Step 4: Add secrets as environment variables

Let's discuss all these steps in details.

## Step 1: Upload dataset to a blob storage container ##

The dataset (training, validation and test sets) should be uploaded to a blob storage container. This will be used to create a datastore (datastores are attached to workspaces and are used to store connection information to Azure storage services so you can refer to them by name and don't need to remember the connection information and secret used to connect to the storage services.) in the next step. The pipelines will also make use of this datastore to read in data and save results from each pipeline step to the storage container.

In order to train a custom Form Recognizer service, the following assets are needed for each image file:

- A `labels.json` file
- An `ocr.json` file

Currently, a set of asset files used to train the Custom Form Recognizer service can be found under the [data/clapperboard_asset_files](../data/clapperboard_asset_files) directory. This directory contains the training images as well as the label and OCR files generated for each image using the sample labeling tool. There are also just the plain set of clapperboard images used for training in the [images/train/clapperboard](../data/images/train/clapperboard) directory in the event that you wish to define a different set of labels. Feel free to use a completely different dataset! Just make sure the asset files required for training on that new dataset are provisioned using the sample labeling tool and uploaded to a blob storage container.

Once the dataset has been uploaded to a blob storage service, a SAS URI will be required to train the Form Recognizer model (this is so that the model can access the dataset that has been created). A storage SAS URI can be created through the Azure portal or through Azure Storage Explorer. For more information regarding the sample labeling tool and how SAS URI's are required to train a Form Recognizer service, refer to [this link.](https://docs.microsoft.com/en-us/azure/cognitive-services/form-recognizer/quickstarts/label-tool?tabs=v2-1)

## Step 2: Setup an Azure Machine Learning Workspace ##

Make sure to set up an Azure Machine Learning subscription through the Azure portal. Once this subscription has been set up you should be able to launch the Azure Machine Learning workspace. Before you launch the AML workspace, make sure to download the `config.json` file from the Azure portal. Store the `config.json` file in the [demo](../demo) directory where the notebooks are located. This `config.json` file will be used for authentication purposes when you attempt to connect to the AML workspace.

Now that an AML subscription has been created, we still need to do two things:

- Setup a compute cluster
- Create and register a datastore

### Setup Compute cluster ###

A compute instance is required to run pipelines within the Azure Machine Learning workspace. In order to create a compute cluster, access the `Compute` tab under the `Manage` section within the AzureML workspace. From here a compute cluster can be created. The following set of paramaters can be configured:

- Virtual Machine Priority
- Virtual Machine Type
- Virtual Machine  Size
- Minimum number of nodes
- Maximum number of nodes
- Idle seconds before scaledown (scaling down nodes)

![Virtual machine specifications](images/compute-cluster-pt1.png =550x)
![Specify min and max nodes](images/compute-cluster-pt2.png =550x)

For the purpose of running the pipelines defined within the notebooks, the default values suffice.

### Create and Register a Datastore ###

In order to make sure pipelines can seamlessly read data from and write data to any Azure storage services (in this case Azure blob storage) it is advisable to create a datastore within the Azure ML workspace. In order to do this, we simply need to click on the `Datastores` tab under the the `Manage` section within the AzureML workspace. From here, we can simply create a datastore using the same storage credentials for the container the datasets have been stored in (storage container from step #1).

![create blob datastore](images/setup-datastore.png =550x)

## Step 3: Create an Azure Form Recognizer and Azure Computer Vision subscription ##

The pipelines utilized within this experiment make use of the following cognitive service:

- Form Recognizer service
- Read API service (under Azure Computer Vision service)

In order to successfully run any experiments, both services need to be provisioned. These services can be accessed and created through the Azure portal. Once a subscription for both the Form Recognizer and Computer Vision service have been created, the credentials should be stored for use in the next step (step #4).

## Step 4: Add Secrets as Environment Variables ##

Now that everything is in place, we simply need to set up our environment variables in order to run the sample notebooks. In the [demo](../demo) directory the following notebooks are available:

- Form Recognizer Training - Run the Form Recognizer Training pipeline
- Form Recognizer Scoring - Run the Form Recognizer Scoring pipeline

In order to run these notebooks, we need a `.env` file and a `config.json` (downloaded from step #2) file.
A [config.example.json](../demo/config.example.json) file is provided in the notebook directory. An actual `config.json` file can be downloaded directly from the Azure portal when you access the Azure Machine learning service. A [.env.example](../demo/.env.example) file is also provided. With this template file, all the keys for the secrets necessary for running the notebooks are defined; they just need to be filled in with their appropriate values. Once the values have been filled in, rename the [.env.example](../demo/.env.example) to a `.env` file and you should be able to run the notebooks without any issues. Here are the definitions for each of the required secrets:

- AML_CLUSTER_CPU_SKU: SKU for the cluster VMs should be provided here (Virtual Machine size)
- AML_CLUSTER_NAME: a name of the cluster (16 symbols max)
- BLOB_DATASTORE_NAME: a name of the datastore that we are using to reference data (name of datastore created in step 1)
- LOCATION: a location of Azure ML (like eastus)
- RESOURCE_GROUP: Azure ML resource group name
- STORAGE_CONTAINER: a container name where we have data to run our experiments
- STORAGE_KEY: a key of the storage where we have our data
- STORAGE_NAME: a name of the storage where we have our data
- SUBSCRIPTION_ID: subscription id
- WORKSPACE_NAME: Azure ML workspace name
- WORKSPACE_SVC_CONNECTION: a service connection name (look at step 2)
- FORM_RECOGNIZER_ENDPOINT: An endpoint for the Form Recognizer resource
- FORM_RECOGNIZER_KEY: Subscription Key for the Form Recognizer resource
- FORM_RECOGNIZER_TRAIN_SAS_URI: SAS URI to train the form recognizer model. The SAS URI generated should point to the same blob container training data is located in.
- FORM_RECOGNIZER_CUSTOM_MODEL_ID: ID for the custom Form Recognizer model that was trained in the Form Recognizer Training pipeline. This can be retrieved from the `model.json` file produced from the training pipeline.
- OCR_KEY: Subscription key for the Azure Computer Vision resource
- OCR_ENDPOINT: Endpoint for the Azure Computer Vision resource
