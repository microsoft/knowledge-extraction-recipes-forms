# Build the runtime from source
ARG HOST_VERSION=3.0.13159
FROM mcr.microsoft.com/dotnet/core/sdk:3.1 AS runtime-image
ARG HOST_VERSION

ENV PublishWithAspNetCoreTargetManifest=false

RUN BUILD_NUMBER=$(echo ${HOST_VERSION} | cut -d'.' -f 3) && \
    git clone --branch v${HOST_VERSION} https://github.com/Azure/azure-functions-host /src/azure-functions-host && \
    cd /src/azure-functions-host && \
    HOST_COMMIT=$(git rev-list -1 HEAD) && \
    dotnet publish -v q /p:BuildNumber=$BUILD_NUMBER /p:CommitHash=$HOST_COMMIT src/WebJobs.Script.WebHost/WebJobs.Script.WebHost.csproj --output /azure-functions-host --runtime linux-x64 && \
    mv /azure-functions-host/workers /workers && mkdir /azure-functions-host/workers && \
    rm -rf /root/.local /root/.nuget /src

# Use bundles 1.3.0 or higher
RUN apt-get update && \
    apt-get install -y gnupg wget unzip && \
    wget https://functionscdnstaging.azureedge.net/public/ExtensionBundles/Microsoft.Azure.Functions.ExtensionBundle/1.3.0/Microsoft.Azure.Functions.ExtensionBundle.1.3.0.zip && \
    mkdir -p /FuncExtensionBundles/Microsoft.Azure.Functions.ExtensionBundle/1.3.0 && \
    unzip /Microsoft.Azure.Functions.ExtensionBundle.1.3.0.zip -d /FuncExtensionBundles/Microsoft.Azure.Functions.ExtensionBundle/1.3.0 && \
    rm -f /Microsoft.Azure.Functions.ExtensionBundle.1.3.0.zip

# Get Python worker 1.1.1
RUN apt-get update && \
    apt-get install -y curl && \
    curl -L -o "/worker.zip" "https://azfunc.visualstudio.com/5293b045-0d0d-4c3a-9abc-d962867a231f/_apis/build/builds/5384/artifacts?artifactName=3.7_LINUX_X64&api-version=5.1&%24format=zip" && \
    unzip /worker.zip -d /worker && \
    rm -f /worker.zip

FROM python:3.7-buster AS app-image

COPY . /app
WORKDIR /app
# https://github.com/MicrosoftDocs/azure-docs/issues/40134
RUN pip3 install --target=".python_packages/lib/site-packages" -r requirements.txt


FROM python:3.7-slim-buster
ARG HOST_VERSION

ENV LANG=C.UTF-8 \
    ACCEPT_EULA=Y \
    AzureWebJobsScriptRoot=/home/site/wwwroot \
    HOME=/home \
    FUNCTIONS_WORKER_RUNTIME=python \
    ASPNETCORE_URLS=http://+:80 \
    DOTNET_RUNNING_IN_CONTAINER=true \
    DOTNET_USE_POLLING_FILE_WATCHER=true \
    HOST_VERSION=${HOST_VERSION}

# Install Python dependencies
RUN apt-get update && \
    apt-get install -y wget && \
    echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections && \
    apt-get update && \
    apt-get install -y apt-transport-https curl gnupg && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/9/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    # Needed for libss1.0.0 and in turn MS SQL
    echo 'deb http://security.debian.org/debian-security jessie/updates main' >> /etc/apt/sources.list && \
    # install necessary locales for MS SQL
    apt-get update && apt-get install -y locales && \
    echo 'en_US.UTF-8 UTF-8' > /etc/locale.gen && \
    locale-gen && \
    # install MS SQL related packages
    apt-get update && \
    apt-get install -y unixodbc msodbcsql17 mssql-tools && \
    # .NET Core dependencies
    apt-get install -y --no-install-recommends ca-certificates \
    libc6 libgcc1 libgssapi-krb5-2 libicu63 libssl1.1 libstdc++6 zlib1g && \
    rm -rf /var/lib/apt/lists/* && \
    # Custom dependencies:
    #  OpenCV dependencies:
    apt-get update && \
    apt-get install -y libglib2.0-0 libsm6 libxext6 libxrender-dev && \
    #  binutils
    apt-get install -y binutils && \
    #  OpenMP dependencies
    apt-get install -y libgomp1

COPY --from=runtime-image ["/azure-functions-host", "/azure-functions-host"]
COPY --from=runtime-image [ "/workers/python", "/azure-functions-host/workers/python" ]
RUN rm -r /azure-functions-host/workers/python/3.7/LINUX/X64
COPY --from=runtime-image [ "/worker/3.7_LINUX_X64", "/azure-functions-host/workers/python/3.7/LINUX/X64" ]
COPY --from=runtime-image [ "/FuncExtensionBundles", "/FuncExtensionBundles" ]

COPY --from=app-image ["/app", "/home/site/wwwroot"]

ENV FUNCTIONS_WORKER_RUNTIME_VERSION=3.7

CMD [ "/azure-functions-host/Microsoft.Azure.WebJobs.Script.WebHost" ]