#!/bin/bash
# Stops the existing nlp_search container if running, rebuilds the image and starts a new container

CONTAINER_NAME="ner_flask_app"

# TODO: Replace "dummy_flask_app" with the actual name of the container
docker container stop `docker ps | awk '/ner_flask_app/ { print $1 }'`
docker image rm -f `docker image ls | awk '/ner_flask_app / { print $3 }'`

./build.sh $CONTAINER_NAME

docker logs --follow `docker run -d -p $FLASK_PORT:$FLASK_PORT -e "FLASK_PORT=$FLASK_PORT" $CONTAINER_NAME`

# To enable Application Insights, switch to the command below
#docker logs --follow `docker run -d -p $FLASK_PORT:$FLASK_PORT -e "FLASK_PORT=$FLASK_PORT" -e "APP_INSIGHTS_KEY=ADD_YOUR_KEY_HERE" $CONTAINER_NAME` &
