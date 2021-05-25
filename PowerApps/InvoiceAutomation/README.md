# Invoice Automation using the Power Platform



Invoice processing is something that every company does, but many are still doing it manually and is very labor intensive.  Not anymore!  This starter kit is intended to use the new "Process and save information from invoices" flow in Power Automate to automatically capture invoice information, save it to a SharePoint document library.  We’ll then use Cognitive Services to extract the invoice line-item information and save it to a SharePoint List.  Finally, Power Apps will allow you to review and complete the processing so it can be integrated with the accounting LOB application.

### Process Overview

Invoices come in several different ways.  Ideally, they would be electronic, if not most scanners/copiers have integration into SharePoint that makes the capture process easy to accomplish.  Here is a typical process overview for most organizations.

![Process Overview](../Invoice%20Automation/images/1-Overview-Process.png)

### SharePoint Schema

To get things started, we need to configure out content types and SharePoint information architecture to accommodate capturing the invoice “header” information, typically located at the top that has non-repeating items such as vendor name, invoice number, date due etc. 

We also need a “line items” list to hold each itemized item that has been purchased.  A typical schema should resemble this:

![SharePoint Schema](../Invoice%20Automation/images/2-Overview-Schema.png)

A few things to keep in mind:

* There should be a content type created for each list, we’ll need this later when configuring the search experience.  It’s best to do this in the SharePoint Admin Center -> Content Services -> Content Type Gallery and then deploy it to the hub the library/list is in.
  
* The relationship between Invoices and Line Items is a 1:many relationship where the InvoiceID column is the SharePoint ID in the Invoices list.

### Automate metadata extraction using Power Automate

Now that we have the plumbing in place to receive the information, time to configure the tools for the metadata extraction. 

![Forms Processing](../Invoice%20Automation/images/3-Overview-MetadataExtraction.png)



Power Automate has a new activity, “Process and save information from invoices” that we’ll use to automatically extract the invoice header information.  This couldn’t be much easier!  I’ve set a few variables that we’ll use later in the flow but simply pass the file contents and it will scan and return values that can be used to update the Invoices metadata.

![Metadata Extraction](../Invoice%20Automation/images/4-Overview-FormsProcessing.png)

![Metadata Extraction 2](../Invoice%20Automation/images/5-Overview-FormsProcessing2.png)

*Once OCRed, the results are automatically available to be mapped to the document library.*

For an overview of the solution please refer to this [blog article]("https://powerusers.microsoft.com/t5/Power-Automate-Community-Blog/Invoice-Automation-using-the-Power-Platform/ba-p/875628) for details.

### Line-Item Extraction using Cognitive Services

Getting the line-item information requires a little more work but Azure Cognitive Services does the hard part for us.

### Configure Form Recognizer in Azure
The ability to OCR a document and have AI determine if there is a table in the document is accomplished using the Form Recognizer service in Azure.  You’ll need to configure this so we can use it in Power Automate.

1. Create a new or use an existing resource group in Azure. (portal.azure.com)
2. Using this resource group add the Form Recognizer service

![Forms Processing](../Invoice%20Automation/images/6-Overview-FormsProcessingSetup.png)

3. Once created there are a few things you’ll need to use the service:
   * Get the Endpoint – we’ll use this in Power Automate to pass our invoice to the service.

    * Get at least 1 of the Keys.  We’ll also need this to call the service.

 ![forms Processing Setup 2](../Invoice%20Automation/images/7-Overview-FormsProcessingSetup2.png)

### Send the invoice to Cognitive Services
Extracting the line-item information (table) from the document requires 2 calls to the Forms Recognition service:

* The first call will take the document and perform an analysis of the contents.  Within Power Automate, make an HTTP call to the endpoint we created in Azure.  This will return a Request ID that we’ll need for the 2nd call.

![Forms Recognizer](../Invoice%20Automation/images/8-Overview-FormsRecognizer.png)

NOTE:  *The HTTP header must contain the Ocp-Apim-Subscription-Key key and the value is the key from the Forms Recognizer service we created in Azure.  The URI is the Endpoint that was created plus the method to analyze the document.*

* I put a delay activity of 10 seconds to give Forms Recognition time to process the document, but the 2nd HTTP call is like the first, except it will return a JSON response of everything it OCRed.
  
![Forms recognizer 2](../Invoice%20Automation/images/9-Overview-FormsRecognizer2.png)

NOTE:  *The key needs to be in the HTTP Header again.  The URI is like the 1st call but contains the URI is decorated with the RequestID output from the 1st call.*

### Parse the JSON body

Using Visual Studio Code and a JSON plugin, you can analyze the JSON output.  Key areas to focus on are:

* The “tables” node.  This will include all the rows and columns the Forms Recognizer service found.
* Rows and Columns in this table node have indexers that tell you where in the table the information is located.
* Pixel coordinates come in handy to know exactly where in the document the information is.
* The “text” node is what were after.  This is the text that was OCRed and returned.

![JSON metadata](../Invoice%20Automation/images/10-Overview-FormsRecognizerJSONOutput.png)

*Row 1, Column 1 (0 based array) in the table…IE invoice lines.*

* Here is a [tool](https://fott-preview.azurewebsites.net/layout-analyze) that you can use to test your documents and see the resulting JSON file contains.  You can then use your favorite parsing tool to get at any information on the document.
  
* To parse the JSON results I opted to write an Azure function to do all the heavy lifting.  The function iterates through all the rows and columns and produces another JSON file with just the column header and value.  The solution is available on [GitHub](https://github.com/Spucelik/InvoiceLineItems).

### Updating the Line-Item list

Taking the JSON response from the Azure function we can now iterate through the rows updating the SharePoint list with the results.  Notice a couple things:

* The Forms Recognizer will return all table rows, even if they are blank.  Make sure to do a check for blank values.
  
* If you are using non-text fields, IE number or currency, then make sure to cast it correctly in the JSON response.  I kept things simple and everything is a string.

![Forms Recognizer Power Automate](../Invoice%20Automation/images/11-Overview-FormsRecognizerPowerAutomate.png)

### PowerApps for Accounting Review
Phew…the hard part is done!  The user interface that accounting will use is done in PowerApps.

![Power App Overview](../Invoice%20Automation/images/12-Overview-PowerApp.png)

Form features include:

* A list of the invoices that mee the Invoice Status value is displayed on the left.
* When selected the invoice is displayed in an image control.
* The invoice properties are displayed on the right so they can be validated.
* If an approver has not been selected, it can be and then routed for approval.

![PowerApp2](../Invoice%20Automation/images/13-Overview-PowerApp2.png)

* Line items can be viewed for the associated invoice.
* If accounting requires a GL code, this can be input and then saved to a collection.
* Once all line items have been processed, a batch can be created for the LOB system and payment.

### Searching for invoices
Users can review the status of any invoice input into SharePoint using the search.

![Search](../Invoice%20Automation/images/14-Overview-Search.png)

* Highly recommended to use the [PnP Modern Search web part](https://github.com/microsoft-search/pnp-modern-search).
* Create a new result source that points to the content type used to create the Invoice library.

![Search Result Source](../Invoice%20Automation/images/15-Overview-SearchResultSource.png)

* A nice feature of the PnP Modern Search web parts is the ability to add columns (Managed columns in search). 
* You can also configure handlebars that allow you to inject code.  Specifically, I wanted to open the invoice in a new tab for easier viewing.  Make sure to include data-interception=”off” value in the link reference.  Otherwise, it will still open in the same tab.

![Search Column Formatting](../Invoice%20Automation/images/16-Overview-SearchColumnFormatting.png)


## Installation Process

There are several components and dependencies that comprise the solution and need to be configured to successfully deploy it in your environnement.

## SharePoint Configuration

Create the Invoice content type in the SharePoint admin center or at the site collection level using the following schema.

![SharePoint Schema](../Invoice%20Automation/images/1-InvoicesContentType.png)

Create the InvoiceLineItems content type in the SharePoint admin center or at the site collection level. 

![SharePoint InvoiceLinesSchema](../Invoice%20Automation/images/2-InvoiceLinesContentType.png)

Publish these content type and in the site collection with the Invoices library and InvoiceLineItems list have been configured.
Create the Invoices library and InvoiceLineItems list in a site collection and assign the content types to the respected library/list.

## Azure Configuration

Create the Azure Forms Recognition Service

* Login to portal.azure.com
* Create a new resource group called "InvoiceAutomation"
* In the new resource group, Add a resource and search for "Form Recognizer"

![Create Form Recognizer Resource](../Invoice%20Automation/images/3-CreateFormRecognizerResource.png)

* Create the new resource

![Create resource](../Invoice%20Automation/images/4-CreateResource.png)

* Provide a name for the instance and pricing tier then click Review + create.

![ResourceName](../Invoice%20Automation/images/4-CreateResource.png)

* Once the resource has been created, navigate to Keys and Endpoint.  
* Copy the Endpoint and one of the Keys.  
* We'll need them later

![Copy Resourece Information](../Invoice%20Automation/images/5-ProvideResoureceName.png)

### Deploy the Azure Function

Place the InvoiceItems.zip file in a local folder and reference it in the PathToZipFile $sourceZipPath variable
The azure function can be deployed using the below PowerShell Script.

```powershell

$location = "East US"
$resourceGroupName = "InvoiceAutomation"
$storageAccountName = "invoicenautomationrg"
$functionName = "InvoiceLineItems"
$sourceZipPath = "<SourceZipPath>\InvoiceLineItems.zip"

Connect-AzAccount

New-AzStorageAccount -ResourceGroupName $resourceGroupName -Name $storageAccountName -Location $location -SkuName "Standard_LRS"
New-AzFunctionApp -Name $functionName -StorageAccountName $storageAccountName -Location $location -ResourceGroupName $resourceGroupName -FunctionsVersion 2 -Runtime DotNet

Publish-AzWebapp -ResourceGroupName $resourceGroupName -Name $functionName -ArchivePath $sourceZipPath
```

## Power Platform Deployment

### Import the solution to PowerApps

Navigate to Power Apps, select Solutions and the environment you want the solution uploaded to.

![PowerApps Solution](../Invoice%20Automation/images/6-PowerAppsSolution.png)

* Browse to the location where the InvoiceProcessing solution has been saved to and import the solution.
* Once the Invoice solution has been uploaded configure the environment variables
* Create a new connection to the SharePoint site collection/list for the Invoices and Invoice Line Items list.
* Navigate to the imported solution "Invoice Processing" and edit each of the Environment variables to your environment

FormsRecognizerURL - In the Azure resource group that was created, choose the InvoiceAutomationFormsRecognizer CognitiveServices type we created above.  In the overview section, copy the Endpoint and use that as the value in the environment variable. (Example:  <https://invoiceautomationformrecognizer.cognitiveservices.azure.com/>

![Forms Recognizer Environment Variable](../Invoice%20Automation/images/7-FormsRecognizerURL.png)

![Forms Recognizer Environment Variable](../Invoice%20Automation/images/7-FormsRecognizerURL.png)


Ocp-Apim-Subscription-Key - in the Keys and Endpoints blade copy one of the keys and use it in this environment variable. (Example:  e3b066e2ee454c2ebb198005...)

![Ocp-Apim](../Invoice%20Automation/images/8-OcpApim.png)

*  InvoiceLineItemsAzureFunction- The URL from the function app that was created in Azure.  (Example:  <https://invoicelineitems.azurewebsites.net/>)

![Line items Azure Function](../Invoice%20Automation/images/9-InvoiceLineItemsAzureFunction.png)  

* InvoiceSiteCollection - the site collection in your tenant where the Invoices library was created (format:  /sites/<SiteCollection>)
*  SiteCollection - update the connection with the site collection the invoices library was created in.

## Test the solution

Once all the assets have been deployed and the configurations have been applied to your environment you can test the solution by first uploading a document into the Invoices document library and monitoring the Power Automate workflow.  Errors may need to be remediated depending on your environment configuration.

Once this has ran successfully, open the PowerApp and view the document that has been uploaded.  