#!/bin/bash
BASE_IMAGE_NAME="ner_flask_app"
BASE_IMAGE_DETAILS=$(docker image ls | awk '/$BASE_IMAGE_NAME/')

if [ -z "$BASE_IMAGE_DETAILS" ]
then
    docker build -t $BASE_IMAGE_NAME --pull --file Dockerfile.base .
else
    echo Found base image: $BASE_IMAGE_DETAILS
fi

if [ -z "$FLASK_PORT" ]; then
    FLASK_PORT=5000
fi

echo "Using port $FLASK_PORT"

docker build -t $1 --file Dockerfile.app . --build-arg FLASK_PORT=$FLASK_PORT
