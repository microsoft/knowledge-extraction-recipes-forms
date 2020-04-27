# Email Processing

Emails are a type of document just like PDFs, Word Documents or scanned document images.

Emails can often be the trigger for important business workflows such as requesting order status, requesting a quote or arranging an appointment.

At scale, companies spend lots of time and effort triaging, processing and responding to emails.

There are tools and techniques that can help companies deal with emails by undertaking the following steps:

1. **Triage**. Work out the intent of the email and which business department or process it should be routed to.
2. **Extraction**. Identification and extraction of key data points from within the email.
3. **Response**. Automatically responding to an email based on the data which was extracted.

It is worth noting that any of the techniques applied to email could also be applied to written free-form letters ('mail' rather than 'email') with the addition or optical character recognition steps prior to the triage.

This document will address the scenario of email recognition and processing with the following high level technology components:

- **[Azure Logic App](https://azure.microsoft.com/en-us/services/logic-apps/)** to trigger on email arrival and do high level process orchestration.
- **[Cognitive Services Language Understanding Intelligence Service (LUIS)](https://www.luis.ai)** for intent detection based on email subject.
- **[Cognitive Services Text Analytics](https://azure.microsoft.com/en-us/services/cognitive-services/text-analytics/)** for entity, key phrase, sentiment and language identification from the email body.
- **Named Entity Recognition** for more accurate and controllable identification of named entities based on either general models or custom models. This is a custom component that has been built as part of this Knowledge Extraction repository. See [the NER folder](/NER/Readme.md) for more details.

## Logic App

A Logic App is a great choice for managing the overall logic flow for email processing for the following reasons:

1. Logic Apps can be triggered on the arrival of email in an Office 365 or Outlook.com mailbox
2. Logic Aps have built-in connectors for parsing and converting content such as converting HTML email body content to plain text
3. Logic apps can easily string multiple api calls to things like Cognitive Services or custom APIs and pass data through the process
4. Logic Apps can reply to emails
5. All of the above with no code

The rest of this article will deal with intent detection and knowledge extraction using other services such as Luis and Text Analytics (being called from the logic app), however Logic Apps provide a wealth of built-in capabilities which are important in this scenario which we'll outline here.

You can see the Luis model at [Email_Processing/EmailProcessingLogicApp.json](Email_Processing/EmailSubjectRecognitionLuis.json) or a screen shot of the designer view at [Email_Processing/EmailProcessingLogicApp-DesignerView.jpg](Email_Processing/EmailProcessingLogicApp-DesignerView.PNG).

### Email service connector

[Connectors](https://docs.microsoft.com/en-us/azure/connectors/apis-list) are a way to connect the logic app to an external service. Logic apps have built in connectors for the following email services:

- [Office 365 Outlook](https://docs.microsoft.com/en-gb/connectors/office365/) - 100's of email operations including triggering on email arrival and sending email via Microsoft Office 365 mailboxes
- [Outlook.com](https://docs.microsoft.com/en-gb/connectors/outlook/) - 100's of email operations including triggering on email arrival and sending email via Microsoft Outlook.com mailboxes
- [Gmail](https://docs.microsoft.com/en-gb/connectors/gmail/) - trigger on email arrival and send emails via Google's Gmail service

There are also connectors for with popular messaging services including [Yammer](https://docs.microsoft.com/en-gb/connectors/yammer/), [Twitter](https://docs.microsoft.com/en-gb/connectors/twitter/), [Slack](https://docs.microsoft.com/en-gb/connectors/slack/), [Microsoft Teams](https://docs.microsoft.com/en-gb/connectors/teams/), [GitHub](https://docs.microsoft.com/en-gb/connectors/github/), [MailChimp](https://docs.microsoft.com/en-gb/connectors/mailchimp/) and many more which may be applicable using the same methods as email.

For this logic app, we have used the Office 365 Outlook connector, but you could substitute whichever connector makes sense for your business, providing it has a trigger which exposes the email/message subject and body. 

The Office 365 Outlook Connector is the trigger for the overall logic app which that the logic app starts whenever and email is received to a specified inbox. In our case we've filtered the subject for keywords, but that is an optional thing (in most scenarios, you'd monitor a specific inbox and process all email).

The connector exposes everything we need from the email, including:

- Subject
- Body
- To/From/CC/BCC
- Attachments
- DateTime
- All the other key email metadata fields

This is the code for using the Office 365 Outlook connector as a trigger:

```json
"When_a_new_email_arrives_(V3)": {
    "inputs": {
        "fetch": {
            "method": "get",
            "pathTemplate": {
                "template": "/v3/Mail/OnNewEmail"
            },
            "queries": {
                "fetchOnlyWithAttachment": false,
                "folderPath": "Inbox",
                "importance": "Any",
                "includeAttachments": false,
                "subjectFilter": "Table53"
            }
        },
        "host": {
            "connection": {
                "name": "@parameters('$connections')['office365']['connectionId']"
            }
        },
        "subscribe": {
            "body": {
                "NotificationUrl": "@{listCallbackUrl()}"
            },
            "method": "post",
            "pathTemplate": {
                "template": "/GraphMailSubscriptionPoke/$subscriptions"
            },
            "queries": {
                "fetchOnlyWithAttachment": false,
                "folderPath": "Inbox",
                "importance": "Any"
            }
        }
    },
    "splitOn": "@triggerBody()?['value']",
    "type": "ApiConnectionNotification"
}
```

### Variables

Variables are a critical tool for developing complex logic apps because they allow us to set and store key data points which we may required throughout the logic app. 

Variables are not always required because the output of every connector is available throughout the logic app, but experience tells us that using variables to store key data points makes them much easier to understand and work with when you are outside the context of the specific connector.

We'll also use variables later on when we enumerate through the Text Analytics output and build-up a string of keywords and entities.

Read more about the Variable connector here: [Store and manage values by using variables in Azure Logic Apps](https://docs.microsoft.com/en-us/azure/logic-apps/logic-apps-create-variables-store-values).

The following code shows the initialisation of the `EmailBody` variable:

```json
"Initialize_variable_EmailBody": {
    "inputs": {
        "variables": [
            {
                "name": "EmailBody",
                "type": "String",
                "value": "@body('Html_to_text')"
            }
        ]
    },
    "runAfter": {
        "Html_to_text": [
            "Succeeded"
        ]
    },
    "type": "InitializeVariable"
},
```

### Content Conversion (Html to Text)

Most emails are sent in either HTML or RTF format, which means it is difficult for services like LUIS or Text Analytics to process the text as they cannot determine the real text from the mark-up.

Thankfully, there is a built in [Content Conversion](https://docs.microsoft.com/en-us/connectors/conversionservice/) connector that converts HTML to plain text.

This connects will gives us a clean, plain text body to work with when we are analysing the body content in later services. 

As with anything that needs to be used outside its directly neighbouring connectors, we use an `EmailBody` variable to store the plain-text output of the Html to Text connector.

The code for this as as follows:

```json
"Html_to_text": {
    "inputs": {
        "body": "<p>@{triggerBody()?['body']}</p>",
        "host": {
            "connection": {
                "name": "@parameters('$connections')['conversionservice']['connectionId']"
            }
        },
        "method": "post",
        "path": "/html2text"
    },
    "runAfter": {},
    "type": "ApiConnection"
},
```

### For Each loops

The Text Analytics service is used to analyse the body message for entities, language and key phrases. In all cases, an array is returned by the text Analytics service.

In the case of this sample, logic app, the end goal is to reply to the initial email with details of how the email was analysed. To do this, we need to cast the array's returned by text Analytics to a comma delimited string. 

Logic Apps have many loops and conditional logic features, but a simple `for each` loop can help us here by enumerating the array and building up a string variable with each key phrase or entity within it.

The code for this is as follows:

```json
"For_each_Key_Phrases": {
    "actions": {
        "Append_to_string_variable": {
            "inputs": {
                "name": "Key Phrases",
                "value": "@{items('For_each_Key_Phrases')}, "
            },
            "runAfter": {},
            "type": "AppendToStringVariable"
        }
    },
    "foreach": "@body('Key_Phrases')?['keyPhrases']",
    "runAfter": {
        "Initialize_variable_Key_Phrases": [
            "Succeeded"
        ]
    },
    "type": "Foreach"
},
```

Read more about the various types of loops here: [Create loops that repeat workflow actions or process arrays in Azure Logic Apps](https://docs.microsoft.com/en-us/azure/logic-apps/logic-apps-control-flow-loops).

## Understanding the intent with LUIS

[Language Understanding Intelligence Service (LUIS)](https://www.luis.ai) is often used for understanding the intent and entities in utterances for conversational systems such as bots. 

However, Luis is really just an API and can be used to extract intent and entities from any short-form text (>500 characters, see [Boundaries for your LUIS model and keys](https://docs.microsoft.com/en-us/azure/cognitive-services/luis/luis-boundaries)), which makes it a perfect system for determining the intent of an email based on the subject.

In this sample, we expect emails to either be and `QuoteRequest` email or a `WhereIsMyOrder` email. These two intent were trained in a Luis model which was published. IN a production system, you'd likely have many more intents.

The Logic App was updated to call Luis using the [Luis Connector](https://docs.microsoft.com/en-us/connectors/luis/) to which the email subject was passed as the `Utterancetext`. This gives us the overall intent of the email which we can use to do conditional logic if required.

You can see the Luis model at [/EmailProcessing/EmailSubjectRecognitionLuis.json](/EmailProcessing/EmailSubjectRecognitionLuis.json).

## Knowledge extraction options

In order to extract knowledge from the main body of the email, there are two main options:

- **[Cognitive Services Text Analytics](https://azure.microsoft.com/en-us/services/cognitive-services/text-analytics/)** a 'black box' service for entity, key phrase, sentiment and language identification from the email body.
- **Named Entity Recognition** for more accurate and controllable identification of named entities based on either general models or custom models. This is a custom component that has been built as part of this Knowledge Extraction repository. See [the NER folder](/NER/Readme.md) for more details.

Both services will provide entity and key phrase extraction from a body of text.

The Cognitive Service is very easy to use and can be easily integrated into a Logic App via the [Text Analytics Connector](https://docs.microsoft.com/en-us/connectors/cognitiveservicestextanalytics/). The Text Analytics service is not trainable which is both a blessing and a curse; it means that it just works out of the box without any configuration or setup. However it is really only suitable for general terminology and cannot (currently) be trained for domain specific language.

The Named Entity Recognition option is effectively a custom code module which can be called in the logic app via a HTTP connector, a custom connector or an Azure Function. This approach will give you more flexibility but will require more setup and some coding.

## In Summary

Emails are just a type of document which can be processed using the same techniques we'd use for any other type of knowledge extraction. However, they are always digital and always have useful metadata that can be used to determine logic based on business rules.

The use of Logic Apps to orchestrate the extraction of knowledge from emails is an obvious choice due to the various triggers from well used email systems and the integrations with services like Luis or Text Analytics.



