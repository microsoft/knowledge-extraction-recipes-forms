base_#!/bin/bash
BASE_IMAGE_NAME="base_image"
BASE_IMAGE_DETAILS=$(docker image ls | awk '/$BASE_IMAGE_NAME/')

if [ -z "$BASE_IMAGE_DETAILS" ]
then
    docker build -t $BASE_IMAGE_NAME --pull --file Dockerfile.base .
else
    echo Found base image: $BASE_IMAGE_DETAILS
fi

docker build -t $1 --file Dockerfile.app .

read -p "press any key"