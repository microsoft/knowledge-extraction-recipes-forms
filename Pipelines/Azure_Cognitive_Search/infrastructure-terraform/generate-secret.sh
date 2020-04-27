#!/bin/bash
set -e

STORAGE_KEY=$(terraform output storage-connection-string)
SEARCH_KEY=$(terraform output azure-search-key)
SEARCH_NAME=$(terraform output azure-search-service-name)

cat ./secrets/ocr-validator.json | \
    jq "(.Azure.Search.ServiceName = \"$SEARCH_NAME\" | .Azure.Search.AdminApiKey = \"$SEARCH_KEY\" | .Azure.Storage.Blob.ConnectionString = \"$STORAGE_KEY\")"
