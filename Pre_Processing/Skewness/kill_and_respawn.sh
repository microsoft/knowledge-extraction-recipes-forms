#!/bin/bash
# Stops the existing nlp_search container if running, rebuilds the image and starts a new container

CONTAINER_NAME="flask_app"

docker container stop `docker ps | awk '/flask_app/ { print $1 }'`
docker image rm -f `docker image ls | awk '/flask_app / { print $3 }'`

./build.sh flask_app

docker build -t $CONTAINER_NAME --file Dockerfile.app .
docker logs --follow `docker run -d -p 5000:5000 $CONTAINER_NAME` &
