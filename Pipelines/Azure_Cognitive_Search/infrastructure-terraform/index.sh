#!/bin/bash
set -e

SEARCH_URL=$(terraform output azure-search-url)
SEARCH_KEY=$(terraform output azure-search-key)
SEARCH_API_VERSION=2019-05-06-Preview

# Start Indexer
curl -d "" -X POST $SEARCH_URL/indexers/cases-blob-indexer/run?api-version=$SEARCH_API_VERSION -H "api-key: $SEARCH_KEY" 
