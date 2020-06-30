# Azure Durable Functions Pipeline - Form Recognizer

This example pipeline utilises the function chaining functionality from Durable Functions. In the function chaining pattern, a sequence of functions executes in a specific order. In this pattern, the output of one function is applied to the input of another function. 

![Function Chaining](https://docs.microsoft.com/en-us/azure/azure-functions/durable/media/durable-functions-concepts/function-chaining.png)

## Sample features

- Remove character boxes using OpenCV
- Call custom Form Recognizer model
- Post processing to clean handwriting output

## How to deploy



