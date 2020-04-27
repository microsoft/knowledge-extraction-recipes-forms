# Flask App Template #

## Dependencies ##

The app is compatible with Python **3.x**. The requirements are listed in [`requirements.txt`](./requirements.txt).

Install the required packages with command:

```bash
pip install -r requirements.txt
```

## API(s) ##

- The **correctSkewness** API gets the location of a form image and the desired output location as input from the body of the **POST** request, corrects the skewness of the form and outputs the location where the corrected image was saved.

Example request to `http://localhost:5000/api/correctSkewness` with body

```json
{
  "path": "BlobStoragePath"
}
```

will result in the following response:

```json
{
  "name": "FormName",
  "outputPath": "BlobStoragePath"
}
```

- The **correctSkewnessBatch** API gets a container name and the desired output container as input from the body of the **POST** request, corrects the skewness of all the forms in the container and outputs the location where the corrected images were saved.

Example request to `http://localhost:5000/api/correctSkewnessBatch` with body

```json
{
  "container": "ContainerName"
}
```

will result in the following response:

```json

{
  "correctedForms":[
    {
      "name": "FormName1",
      "outputPath": "BlobStoragePath1"
    },
    //...
    {
      "name": "FormNameN",
      "outputPath": "BlobStoragePathN"
    }
  ]
}
```

## Running the unit tests ##

To run the unit tests execute command:

```bash
python -m pytest src
```

## Building and running the Docker image locally ##

When developing the Docker image, it saves a lot of time to separate the fixed dependencies, such as Python itself and various packages, from the code that is being developed. This is achieved by creating two Dockerfiles - one for the base image with the dependencies and another for the actual application code. The latter will be built on top of the base image.

To build the images, run the [Build script](./build.sh):

```bash
./build.sh
```

The Docker CLI commands executed by the script are the following:

```bash
docker build -t base_image --pull --file Dockerfile.base .
```

```bash
docker build -t flask_app --file Dockerfile.app .
```

`Dockerfile.app` will reference the base image with name `base_image` in the example above.

To run the Docker container:

```bash
docker run -d -p 5000:5000 flask_app
```

> **Note**
>
> [`kill_and_respawn.sh`](./kill_and_respawn.sh) script, tearing down the previous image and creating/launching new one, is provided for convenience.

### Troubleshooting ###

Once you run a container, it will be associated with a newly generated container ID. After executing the `docker run` command the ID is printed to `stdout`:

```bash
$ docker run -d -p 5000:5000 flask_app
2764f728a06fe7bfef316feb9f1875d6cc40db73820163cab9ba666eac539843
```

You can also check the container ID with `docker ps` command:

```bash
$ docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                    NAMES
2764f728a06f        flask_app         "/bin/sh -c 'python …"   3 seconds ago       Up 1 second         0.0.0.0:5000->5000/tcp   heuristic_hugle
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
docker logs --follow `docker run -d -p 5000:5000 flask_app`
```

Sometimes it's useful to peek inside the container. You can use the command `docker exec -it <container name> /bin/bash` to get a bash shell in the container. If you are a Windows user, note that this command may not work in **Git Bash**.

#### Flask debug mode ####

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

Back to the [Pre-Processing section](../README.md)