# Receipts

Receipt recognition with Form Recognizer

One of the latest [Cognitive Services](https://azure.microsoft.com/en-gb/services/cognitive-services/) is [Form Recognizer](https://azure.microsoft.com/en-gb/services/cognitive-services/form-recognizer/) which is a preview API built to help extract data from electronic forms.

Specifically, Form Recognizer can extract text, key/value pairs and tables from documents and receipts.

There are two modes of operation for Forms Recognizer:

1. [Analyze Form](https://westus2.dev.cognitive.microsoft.com/docs/services/form-recognizer-api/operations/AnalyzeWithCustomModel): A trainable mode which requires at least 5 sample documents/forms of the same type. It uses transfer learning algorithms to build a recognition model from the samples. You can use this model to extract data from new forms of the same type.
2. [Analyze Receipt](https://westus2.dev.cognitive.microsoft.com/docs/services/form-recognizer-api/operations/AnalyzeReceipt): A pre-built model which cannot be trained (it is pre-trained by Microsoft). Analyze Receipt will extract multiple key/value pairs as well as optical character recognition (OCR) data from typical retail receipts.

I've been working with a customer that uses general retail receipts for market research purposes and had a requirement to extract specific data points from photos of receipts. I did some research around the Analyze Receipt function and this article is what I learnt ....

## What gets extracted

There are common fields found in most retail receipts such as retailer, amount, date etc.

The receipts model looks to extract these common fields, specifically it can identify the following:

- MerchantName
- MerchantPhoneNumber
- MerchantAddress
- TransactionDate
- TransactionTime
- Total
- SubTotal
- Tax

Interestingly, the receipts model does not contain any special functionality around recognizing line items within a receipt.

The raw OCR data for lines items is contained, but they are not explicitly extracted out as 'understood fields'. See the Missing Features section later in this article for details.

The OCR results are the same result that you'd get from the [Cognitive Services Computer Vision API](https://azure.microsoft.com/en-us/services/cognitive-services/computer-vision/).

## How do I use it

Because Forms Recognizer is still in private preview, you must request access via the [Form Recognizer access request form](https://aka.ms/FormRecognizerRequestAccess). When access is granted, you should receive an email with a specific link to create the Form Recognizer resource in your Azure subscription.

When I wrote this article (September 2019), the link was as follows: <https://portal.azure.com/?microsoft_azure_marketplace_ItemHideKey=microsoft_azure_cognitiveservices_formUnderstandingPreview#create/Microsoft.CognitiveServicesFormRecognizer>

> Note: You will not find Forms Recognizer by searching or browsing in the 'Create' menu whilst it is still a preview service.

Once you have a provisioned the service, you'll have your own service endpoint which will be something like `https://whateveryoucalledit.cognitiveservices.azure.com`. There will also be a key that you'll need; you can get both of these by looking in the Azure Portal in the `Quick Start` section for the resource.

The Analyze Receipt function uses a two part approach where you initially post the [Analyze Receipt](https://westus2.dev.cognitive.microsoft.com/docs/services/form-recognizer-api/operations/AnalyzeReceipt) request and then check [Get Receipt Result](https://westus2.dev.cognitive.microsoft.com/docs/services/form-recognizer-api/operations/GetReceiptResult) until you get a `200` response (I suspect that this may be tidied up into a single call before the service goes into general availability).

You can `POST` an image containing a receipt with your key in the `Ocp-Apim-Subscription-Key` header to [Analyze Receipt](https://westus2.dev.cognitive.microsoft.com/docs/services/form-recognizer-api/operations/AnalyzeReceipt). The response will contain a header called `Operation-Location` which contains a URL which you will need to get the result.

When you have `Operation-Location` you can send a `GET` request to whatever the value of `Operation-Location`  was (see [Get Receipt Result](https://westus2.dev.cognitive.microsoft.com/docs/services/form-recognizer-api/operations/GetReceiptResult)). The response will be a JSON payload containing all the recognized data.

The response is split into two sections:

- **recognitionResults**: This is the raw OCR output which contains the same output that you would get from the standard [Computer Vision API](https://azure.microsoft.com/en-gb/services/cognitive-services/computer-vision/#detect-text). This is a series of lines containing identified words with their 'bounding box' which can be used to determine their position within the image. This can be used to find fields that the receipt model does not automatically extract, providing you know where they will appear within the image.
- **understandingResults**: These are the specifically recognized key/value pairs that the receipt model looks for (merchantName, total etc). This is the `understandingResults` section from [this image](https://raw.githubusercontent.com/martinkearn/Content/master/Demos/Machine%20Learning%20and%20Cognitive/ML%20Supporting%20Files/Receipts/TheCurator-3140.jpg)

![](https://raw.githubusercontent.com/martinkearn/Content/master/Demos/Machine%20Learning%20and%20Cognitive/ML%20Supporting%20Files/Receipts/TheCurator-3140-Thumb.jpg)

```json
"understandingResults": [
        {
            "pages": [
                1
            ],
            "fields": {
                "Subtotal": null,
                "Total": {
                    "valueType": "numberValue",
                    "value": 28.4,
                    "text": "28.40",
                    "elements": [
                        {
                            "$ref": "#/recognitionResults/0/lines/23/words/0"
                        },
                        {
                            "$ref": "#/recognitionResults/0/lines/23/words/1"
                        },
                        {
                            "$ref": "#/recognitionResults/0/lines/23/words/2"
                        }
                    ]
                },
                "Tax": null,
                "MerchantAddress": null,
                "MerchantName": {
                    "valueType": "stringValue",
                    "value": "The Curator",
                    "text": "The Curator",
                    "elements": [
                        {
                            "$ref": "#/recognitionResults/0/lines/0/words/0"
                        },
                        {
                            "$ref": "#/recognitionResults/0/lines/0/words/1"
                        }
                    ]
                },
                "MerchantPhoneNumber": null,
                "TransactionDate": {
                    "valueType": "stringValue",
                    "value": "2019-02-19",
                    "text": "19 Feb 2019",
                    "elements": [
                        {
                            "$ref": "#/recognitionResults/0/lines/7/words/0"
                        },
                        {
                            "$ref": "#/recognitionResults/0/lines/7/words/1"
                        },
                        {
                            "$ref": "#/recognitionResults/0/lines/7/words/2"
                        }
                    ]
                },
                "TransactionTime": {
                    "valueType": "stringValue",
                    "value": "14:46:00",
                    "text": "14:46",
                    "elements": [
                        {
                            "$ref": "#/recognitionResults/0/lines/7/words/3"
                        }
                    ]
                }
            }
        }
    ]
```

You can see the official quick-start steps for testing the service out here: <https://docs.microsoft.com/en-us/azure/cognitive-services/form-recognizer/quickstarts/curl-receipts>

## Results, accuracy & findings

I tested the receipts API with several different receipts from general purpose retailers in UK ranging from major high street stores like Halfords to airport bars and restaurants. You can see them all for yourself in my [GitHub Content respository](https://github.com/martinkearn/Content/tree/master/Demos/Machine%20Learning%20and%20Cognitive/ML%20Supporting%20Files/Receipts)

> NOTE: My testing was done on the preview API in July 2019 and I expect the results and accuracy to improve over time as the service matures. Your mileage may vary!

I found that generally speaking, the API was able to accurately extract some of the `understandingResults` information from each receipt but it was rarely able to extract every field.

I also found that the fields that were identified tended to vary by receipt and were inconsistent.

The accuracy was generally good, but not perfect. I noticed some of the following mistakes:

- `Total` being mistaken for `SubTotal`
- Currency marks being mistaken for numbers
- Text like table number, order number etc being mistaken for other fields

## Missing Features

The receipts API is a great start but has some missing features for me which would really make it useful and  more complete.

### Line item recognition

The big gap in the existing API is that it does not extract the line items on the receipt as part of the  `understandingResults` data set.

I'd love to see each item extracted into an array with the following properties:

- Item description/sku/title
- Quantity
- Total

At the time of writing, the only way to deal with line items is to use the basic OCR results (the `recognitionResults`) and build some custom logic to determine line items within the receipt.

The [Analyze Form function](https://westus2.dev.cognitive.microsoft.com/docs/services/form-recognizer-api/operations/AnalyzeWithCustomModel) of the Forms Recognizer API can deal with table recognition and extraction so you may be able to combine both functions to get the line items as well as the `understandingResults`. However, this requires model training and would only be possible for specific receipt 'shapes'; it would not be possible for all receipts (which is the whole point of the receipts API).

### Additional fields

In bars and restaurants, a tip is often incorporated into the overall bill and many expenses systems require that this is itemized separately from the overall bill.

It would be helpful if the receipts API were able to extract a tip/gratuity as part of the `understandingResults` data set.

There are other fields that could be useful too, including:

- Merchant website
- Cash register number
- Loyalty programme / customer number

### Resolutions for multiple matches

Other Cognitive Services such as [Luis](https://azure.microsoft.com/en-us/services/cognitive-services/language-understanding-intelligent-service/) uses a concept called Resolutions to provide alternative options for data points that it cannot fully resolved, the classic example is that if you say "Saturday", Luis will offer the Saturday just gone and next Saturday as resolutions.

Resolutions empower developers to write logic that chooses the right result for the app based on some business logic.

It would be great to see the receipt API offer a similar feature for the `understandingResults` data set.

For example, `Total` and `SubTotal` often get mixed up. If there were Resolutions available, there could be logic that says that `Total` must always be more than `SubTotal` thus allowing the application to pick the right results.

## In Summary

The Forms Recognizer is a very powerful new API which is able to extract meaningful information from documents and receipts.

At the time of writing there are limitations which will hopefully get resolved but even with the limitations, the receipts API can form the basis of a receipt data extraction system.

The fact that the receipt API also give you the OCR results as well as the specially recognized data points means that you can add logic to extract additional information as required.

## Further Reading

You may find these resources useful.

- [Cognitive Services Form Recognizer Product Page](https://azure.microsoft.com/en-us/services/cognitive-services/form-recognizer/)
- [Microsoft Azure Docs > Forms Recognizer Overview](https://docs.microsoft.com/en-us/azure/cognitive-services/form-recognizer/overview)
- [Microsoft Azure Docs > Quickstart: Extract receipt data using the Form Recognizer REST API with cURL](https://docs.microsoft.com/en-us/azure/cognitive-services/form-recognizer/quickstarts/curl-receipts)
- [Microsoft Azure Docs > Quickstart: Extract receipt data using the Form Recognizer REST API with Python](https://docs.microsoft.com/en-us/azure/cognitive-services/form-recognizer/quickstarts/python-receipts)
- [Form Recognizer API reference](https://westus2.dev.cognitive.microsoft.com/docs/services/form-recognizer-api/operations/AnalyzeWithCustomModel)
