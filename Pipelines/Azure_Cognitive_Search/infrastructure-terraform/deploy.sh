#!/bin/bash
set -e

# Create Infrastructure
terraform init ./terraform
terraform apply ./terraform

STORAGE_KEY=$(terraform output storage-connection-string)
STORAGE_CONTAINER=$(terraform output storage-container)
COGNITIVE_ACCOUNT_ID=$(terraform output cognitive-service-id)
COGNITIVE_ACCOUNT_KEY=$(terraform output cognitive-service-key)
SEARCH_URL=$(terraform output azure-search-url)
SEARCH_KEY=$(terraform output azure-search-key)
SEARCH_API_VERSION=2019-05-06-Preview

# Create Index
curl -d "@search/index.json" -X POST $SEARCH_URL/indexes?api-version=$SEARCH_API_VERSION -H "api-key: $SEARCH_KEY" -H "Content-Type: application/json"
# Create Data Source
jq "(.credentials.connectionString = \"$STORAGE_KEY\" | .container.name = \"$STORAGE_CONTAINER\")" ./search/data-source.json | \
    curl -d @- -X POST $SEARCH_URL/datasources?api-version=$SEARCH_API_VERSION -H "api-key: $SEARCH_KEY" -H "Content-Type: application/json"
# Create Skillset
jq "(.cognitiveServices.description = \"$COGNITIVE_ACCOUNT_ID\" | .cognitiveServices.key = \"$COGNITIVE_ACCOUNT_KEY\")" ./search/skillset.json | \
    curl -d @- -X POST $SEARCH_URL/skillsets?api-version=$SEARCH_API_VERSION -H "api-key: $SEARCH_KEY" -H "Content-Type: application/json"
# Create Indexer
curl -d "@search/indexer.json" -X POST $SEARCH_URL/indexers?api-version=$SEARCH_API_VERSION -H "api-key: $SEARCH_KEY" -H "Content-Type: application/json"
