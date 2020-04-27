# Named Entity Recognition

## Dependencies

The app is compatible with Python **3.x**. The requirements are listed in [`requirements.txt`](./requirements.txt).

Install the required packages with command:

```bash
pip install -r requirements.txt
```

## APIS

* RunNerAPI - Run a trained Named Entity Recognition model on a document

This app gets its inputs from both the URI and the body of the **POST** request.

Example request to `http://localhost:5000/api/ner_eval?model=<pretrained_model_name>` with body (the expected content type is `application/json`)

```json
{
 "doc": "<doc to extract named entities from>",
 "ent_types": ["ORG","GPE"]
}
```

will result in the following response:

```json
"{\"Company Ltd.\": \"ORG\"}"
```

* NerBenchmarkAPI - Benchmark a trained named entity model on an evaluation set

This app gets its inputs from both the URI and the body of the **POST** request.

Example request to `http://localhost:5000/api/ner_eval?model=<pretrained_model_name>` with body (the expected content type is `application/json`)

```json
{
    "uas": 0,
    "las": 0,
    "ents_p": 80,
    "ents_r": 100,
    "ents_f": 88.8888888888889,
    "ents_per_type": {
        "MONEY": {
            "p": 0,
            "r": 0,
            "f": 0
        },
        "GPE": {
            "p": 100,
            "r": 100,
            "f": 100
        },
        "ORG": {
            "p": 100,
            "r": 100,
            "f": 100
        }
    },
    "tags_acc": 0,
    "token_acc": 100,
    "textcat_score": 0,
    "textcats_per_cat": {}
}
```

will result in the following response:

```json
"{\"Company Ltd.\": \"ORG\"}"
```

## Running the unit tests

To run the unit tests execute command:

```bash
python -m pytest src
```

## Getting started with the template

The template is ready to go out-of-the-box. However, when building a new service using the template, you will want to change several things starting with the **application/container name**:

  1. If you are using the utility script, [`kill_and_respawn.sh`](./kill_and_respawn.sh) (see the next section for more details), edit the first effective line (`CONTAINER_NAME="dummy_flask_app"`) to change the container name (note that the tear down commands in the script need to be changed separately)
  2. [app.py](./app.py) contains a "constant" `APPLICATION_NAME` that is used by Application Insights

The **Flask app port** is defined by an environment variable `FLASK_PORT` - in [build.sh](./build.sh):

```sh
docker build -t $1 --file Dockerfile.app . --build-arg FLASK_PORT=$FLASK_PORT
```

The default value is `5000`.

The template has **Application Insights tracing** implemented. To enable Application Insights, you must provide the instrumentation key as an environment variable (see [`kill_and_respawn.sh`](./kill_and_respawn.sh) for reference):

```sh
docker run -d -p <port (range> -e "FLASK_PORT=$FLASK_PORT" -e "APP_INSIGHTS_KEY=ADD_YOUR_KEY_HERE" <container name>
```

If no instrumentation key is provided, the logger will use the default handler.

## Building and running the Docker image locally

When developing the Docker image, it saves a lot of time to separate the fixed dependencies, such as Python itself and various packages, from the code that is being developed. This is achieved by creating two Dockerfiles - one for the base image with the dependencies and another for the actual application code. The latter will be built on top of the base image.

To build the images, run the [Build script](./build.sh):

```bash
./build.sh
```

The Docker CLI commands executed by the script are the following:

```bash
docker build -t dummy_base_image --pull --file Dockerfile.base .
```

```bash
docker build -t dummy_flask_app --file Dockerfile.app .
```

`Dockerfile.app` will reference the base image with name `dummy_base_image` in the example above.

To run the Docker container:

```bash
docker run -d -p 5000:5000 dummy_flask_app
```

> **Note**
>
> [`kill_and_respawn.sh`](./kill_and_respawn.sh) script, tearing down the previous image and creating/launching new one, is provided for convenience.

### Troubleshooting

Once you run a container, it will be associated with a newly generated container ID. After executing the `docker run` command the ID is printed to `stdout`:

```bash
$ docker run -d -p 5000:5000 dummy_flask_app
2764f728a06fe7bfef316feb9f1875d6cc40db73820163cab9ba666eac539843
```

You can also check the container ID with `docker ps` command:

```bash
$ docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                    NAMES
2764f728a06f        dummy_flask_app         "/bin/sh -c 'python …"   3 seconds ago       Up 1 second         0.0.0.0:5000->5000/tcp   heuristic_hugle
```

After starting the container you can monitor it using the `docker logs` command:

```bash
$ docker logs --follow 2764f728a06fe7bfef316feb9f1875d6cc40db73820163cab9ba666eac539843
 * Serving Flask app "flask_app" (lazy loading)
 * Environment: production
   WARNING: Do not use the development server in a production environment.
   Use a production WSGI server instead.
 * Debug mode: on
```

If you find copy-pasting the container ID too tiresome, you can type:

```bash
docker logs --follow `docker run -d -p 5000:5000 dummy_flask_app`
```

Sometimes it's useful to peek inside the container. You can use the command `docker exec -it <container name> /bin/bash` to get a bash shell in the container. If you are a Windows user, note that this command may not work in **Git Bash**.

#### Flask debug mode

To enable Flask debug mode, rebuild the image after changing the value of `FLASK_DEBUG_MODE` in [`Dockerfile.app`](./Dockerfile.app):

```bash
ENV FLASK_DEBUG_MODE=1
```

Naturally, value `0` will equal `False` and `1` will equal `True`.

In case the Flask app fails at launch with the error message shown below, turn the debug mode off (`ENV FLASK_DEBUG_MODE=0`):

```bash
 * Serving Flask app "flask_app" (lazy loading)
 * Environment: production
   WARNING: Do not use the development server in a production environment.
   Use a production WSGI server instead.
 * Debug mode: on

 ...

: No such file or directory
```

Back to the [Training section](../README.md)
