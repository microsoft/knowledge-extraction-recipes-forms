# Azure Durable Functions Pipeline - Form Recognizer

This example pipeline utilises the function chaining functionality from Durable Functions. In the function chaining pattern, a sequence of functions executes in a specific order. In this pattern, the output of one function is applied to the input of another function.

![Function Chaining](https://docs.microsoft.com/en-us/azure/azure-functions/durable/media/durable-functions-concepts/function-chaining.png)

## Features

This example has the following functionality built-in, but could easily be extended by adding your own functions.

- Triggered by new files on a blob storage
- Remove character boxes using OpenCV
- Call Form Recognizer service via a temporary SAS token
- Post processing to clean output

## How to develop
[todo, explain Dev Containers in VCode]

```json
    "StorageAccount": ""
    "FormRecognizer_Endpoint": ""
    "FormRecognizer_SubscriptionKey": ""
    "FormRecognizer_ModelId": ""
```

## How to deploy
[todo, point to VSCode deploy docs]
