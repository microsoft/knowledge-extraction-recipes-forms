# Infrastructure as a Code

## Introduction 
This project creates a basic Cognitive Search infrastructure on Azure using Terraform. It deploys the following resources:

* [Blob Storage](https://docs.microsoft.com/en-us/azure/storage/blobs/storage-blobs-overview)
* [Cognitive Services](https://docs.microsoft.com/en-us/azure/cognitive-services/welcome)
* [Azure Search](https://docs.microsoft.com/en-us/azure/search/)

After creating the infrastructure, this repository also contains scripts that operates at Azure Search data plan level, creating:

* [Index](https://docs.microsoft.com/en-us/rest/api/searchservice/create-index)
* [Data Source](https://docs.microsoft.com/en-us/rest/api/searchservice/create-data-source)
* [Skillset](https://docs.microsoft.com/en-us/rest/api/searchservice/create-skillset)
* [Indexer](https://docs.microsoft.com/en-us/rest/api/searchservice/create-indexer)

## Getting Started

### Requirements

* Bash
* [curl](https://www.luminanetworks.com/docs-lsc-610/Topics/SDN_Controller_Software_Installation_Guide/Appendix/Installing_cURL_for_Ubuntu_1.html)
* [jq](https://stedolan.github.io/jq/download/)
* [Terraform](https://learn.hashicorp.com/terraform/getting-started/install.html)

### Usage

To create the infrastructure, you can use:

```bash
./deploy.sh
```

## Azure Search - Details

This template deploys a blob storage account, with a single container called `pdf`. You can use this container to upload any documents you wish to be indexed.

> You can use Azure Portal, [Azure Storage Explorer](https://azure.microsoft.com/en-us/features/storage-explorer/) or [AzCopy](https://docs.microsoft.com/en-us/azure/storage/common/storage-use-azcopy-v10) to upload your documents to the blob storage account.

The script creates a [Data Source](./search/data-source.json) on Search, which is an abstraction pointing to the blob storage account.

Also, the script creates a [Skillset](./search/skillset.json), which is a set of well defined processing steps the incoming data/content should receive before being indexed on Search. These steps involves extracting entities (People, Organizations, Locations and Keyphrases) and applying OCR to image based documents. This process is called [Cognitive Search](https://docs.microsoft.com/en-us/azure/search/cognitive-search-concept-intro). The script deploys a dedicated Cognitive Services key and link it with the Skillset.

The script also creates an [Index](./search/index.json), which is defined as:

> An index is the primary means of organizing and searching documents in Azure Search, similar to how a table organizes records in a database. Each index has a collection of documents that all conform to the index schema (field names, data types, and attributes)

The deployed index has the following schema:

| Property              | Type     | Description                                                                                |
|-----------------------|----------|--------------------------------------------------------------------------------------------|
| Id                    | string   | Primary key. Is a base64 transformation of property metadata_storage_name.                 |
| content               | string   | Original extracted content (only text) from documents.                                     |
| merged_content        | string   | Content merged with OCR results.                                                           |
| metadata_storage_path | string   | Blob document path/URL.                                                                    |
| People                | string[] | Cognitive Search people extraction result.                                                 |
| Organizations         | string[] | Cognitive Search organizations extraction result.                                          |
| Locations             | string[] | Cognitive Search locations extraction result.                                              |
| Keyphrases            | string[] | Cognitive Search keyphrases extraction result.                                             |
| caseId                | string   | An ID to relate different documents which belongs to a same business case.                 |
| role                  | string   | Document role, can be one of the following: "Expected" or "Actual". Used for comparisons. |

> Other minor properties were hidden for clarity

The last piece create on Search is an [Indexer](./search/indexer.json):

> An **indexer** crawls an external **data source** (blob container), extracts information, serializes it as JSON documents, calls processing steps defined in **skillsets** and stores the text in an Azure Search **index**.

## Other Scripts

* Trigger an Indexer:

```shell
./index.sh
```

* Generate JSON [secrets](../ocr-validator/OCR/OCR.Validator.Web/appsettings.json) for `OCR.Validator.Web` project:

```shell
./generate-secret.sh
```