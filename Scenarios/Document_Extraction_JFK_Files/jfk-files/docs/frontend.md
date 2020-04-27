# JFK Front-end

The front-end is built with Node.js, TypeScript and React. It communicates with: 

- Azure Search to run queries and render OCR images + metadata (e.g. file name)
- Facet Graph Nodes function to render the graph with all related entities in the Azure Search query

All environment variables are in a .env file.
Components of each page are under pages folder.
Graph rendering is under graph-api folder.

## Prerequisites

- Install [Node.js](https://nodejs.org/en/download/)

## Getting Started

Install all dependencies: 

```sh
npm install
```

Update the `.env` file:

```
NODE_ENV=development
PORT=8083
SEARCH_CONFIG_PROTOCOL=https
SEARCH_CONFIG_SERVICE_NAME=[SearchServiceName]
SEARCH_CONFIG_SERVICE_DOMAIN=[SearchServiceDomain]
SEARCH_CONFIG_SERVICE_PATH=indexes/[IndexName]/docs
SEARCH_CONFIG_API_VER=[SearchServiceApiVersion]
SEARCH_CONFIG_API_KEY=[SearchServiceApiKey]
SUGGESTION_CONFIG_PROTOCOL=https
SUGGESTION_CONFIG_SERVICE_NAME=[SearchServiceName]
SUGGESTION_CONFIG_SERVICE_DOMAIN=[SearchServiceDomain]
SUGGESTION_CONFIG_SERVICE_PATH=indexes/[IndexName]/docs/autocomplete
SUGGESTION_CONFIG_API_VER=[SearchServiceApiVersion]
SUGGESTION_CONFIG_API_KEY=[SearchServiceApiKey]
FUNCTION_CONFIG_PROTOCOL=https
FUNCTION_CONFIG_SERVICE_NAME=[AzureFunctionName]
FUNCTION_CONFIG_SERVICE_DOMAIN=azurewebsites.net
FUNCTION_CONFIG_SERVICE_PATH=api/facet-graph-nodes
FUNCTION_CONFIG_SERVICE_AUTH_CODE_PARAM=code=[AzureFunctionDefaultHostKey]
```

Build and run the application: 

```sh
npm run start:dev
```

## Deploying the web app

In order to deploy the application on Azure, we need to package its content on the `dist` folder. Run the following command to build and package the application:

```sh
  npm run build:prod
```

Now copy the content generated from the _dist_ folder into your web server.

 > This process can be easily automated and enclosed on a CD enviroment.
