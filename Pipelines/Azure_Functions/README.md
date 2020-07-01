# Form Recognizer with Azure Functions

Scoring a form in more complex scenarios usually requires a pre- and post-processing which could be automated. Think of actions like remove boxes from the input form using OpenCV, classifying the form type, sending the form to the Form Recognizer service and cleaning of the output.

Azure Functions is an event driven, compute-on-demand experience that extends the existing Azure application platform with capabilities to implement code triggered by events occurring in Azure or third party service as well as on-premises systems.

- Pay-per-use pricing model, pay only for the time spent running your code. ([Consumption hosting plan](https://docs.microsoft.com/en-us/azure/azure-functions/functions-overview#pricing))
- Super scalable, scale out on demand
- Durable Functions enable you to write stateful functions in a serverless compute environment
- Multiple triggers, input and output bindings supported by default
- Open-source, the Functions runtime is open-source and available on GitHub

## Using Form Recognizer with Azure Functions

Use Form Recognizer with Azure Functions to orchestrate a flow for scoring forms.

### Example pipelines using Azure Functions

- [`python_durable_functions`](python_durable_functions/README.md) - an end-to-end workflow including OpenCV image processing and post-processing on Azure Functions for Python

Back to the [pipelines overview](../README.md)
