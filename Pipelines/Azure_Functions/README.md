# Form Recognizer with Azure Functions

Scoring a form in more complex scenarios usually requires a pre- and postprocessing which could be automated. Think of actions like cleaning the input form using OpenCV, classifying the form type, sending the form to the Form Recognizer service and cleaning the output.

Azure Functions is an event driven, compute-on-demand experience that extends the existing Azure application platform with capabilities to implement code triggered by events occurring in Azure or third party service as well as on-premises systems.

- Pay per execution
- Super scalable, scale out to max 200 instances on demand
- Durable Functions enable you to write stateful functions in a serverless compute environment

## Using Form Recognizer with Azure Functions

Use Form Recognizer with Azure Functions to orchestrate a flow for scoring images.

### Prerequisites

- Azure Subscription \- [Create one for free](https://azure.microsoft.com/free)

## Example pipelines using Azure Functions

- [`python_durable_functions`](python_durable_functions/README.md) - showing a end-to-end workflow including OpenCV processing on Azure Functions for Python
