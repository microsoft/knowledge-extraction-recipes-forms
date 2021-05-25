# Invoice Automation using the Power Platform

## Overview

Invoice processing is something that every company does, but many are still doing it manually and is very labor intensive.  Not anymore!  This starter kit is intended to use the new "Process and save information from invoices" flow in Power Automate to automatically capture invoice information, save it to a SharePoint document library.  We’ll then use Cognitive Services to extract the invoice line-item information and save it to a SharePoint List.  Finally, Power Apps will allow you to review and complete the processing so it can be integrated with the accounting LOB application.


For an overview of the solution please refer to this [blog article]("https://powerusers.microsoft.com/t5/Power-Automate-Community-Blog/Invoice-Automation-using-the-Power-Platform/ba-p/875628) for details.

## Installation Process

There are several components and dependencies that comprise the solution and need to be configured to successfully deploy it in your environnement.

## SharePoint Configuration

<ol>
<li>
Create the Invoice content type in the SharePoint admin center or at the site collection level using the following schema.
</li>

 ![SharePoint Schema](images/1-InvoicesContentType.png)

<li>Create the InvoiceLineItems content type in the SharePoint admin center or at the site collection level.</li>

![SharePoint InvoiceLinesSchema](images/2-InvoiceLinesContentType.png)

<li>Publish these content type and in the site collection with the Invoices library and InvoiceLineItems list have been configured.</li>
<li>Create the Invoices library and InvoiceLineItems list in a site collection and assign the content types to the respected library/list.</li>
</ol>

## Azure Configuration

<ol>
<li>Create the Azure Forms Recognition Service
    <ol>
        <li>Login to portal.azure.com</li>
        <li>Create a new resource group called "InvoiceAutomation"</li>
        <li>In the new resource group, Add a resource and search for "Form Recognizer"</li>

![Create Form Recognizer Resource](images/3-CreateFormRecognizerResource.png)
        <li>Create the new resource</li>
![Create resource](images/4-CreateResource.png)
        <li>Provide a name for the instance and pricing tier then click Review + create.</li>
![ResourceName](images/5-ProvideResoureceName.png)
        <li>Once the resource has been created, navigate to Keys and Endpoint.  Copy the Endpoint and one of the Keys.  We'll need them later</li>
![Copy Resourece Information](images/5-ProvideResoureceName.png)
    </ol>

</li>
<li>
Deploy the Azure Function
    <ol>
        <li>Place the InvoiceItems.zip file in a local folder and reference it in the PathToZipFile $sourceZipPath variable</li>
        <li>The azure function can be deployed using the below PowerShell Script.

        $location = "East US"
        $resourceGroupName = "InvoiceAutomation"
        $storageAccountName = "invoicenautomationrg"
        $functionName = "InvoiceLineItems"
        $sourceZipPath = "<SourceZipPath>\InvoiceLineItems.zip"

        Connect-AzAccount

        New-AzStorageAccount -ResourceGroupName $resourceGroupName -Name $storageAccountName -Location $location -SkuName "Standard_LRS"
        New-AzFunctionApp -Name $functionName -StorageAccountName $storageAccountName -Location $location -ResourceGroupName $resourceGroupName -FunctionsVersion 2 -Runtime DotNet

        Publish-AzWebapp -ResourceGroupName $resourceGroupName -Name $functionName -ArchivePath $sourceZipPath

</li>
</ol>
</li>
</ol>

## Power Platform Deployment

<ol>
    <li>Import the solution to PowerApps</li>
    <ol>
        <li>Navigate to Power Apps, select Solutions and the environment you want the solution uploaded to.</li>

![PowerApps Solution](images/6-PowerAppsSolution.png)
        <li>Browse to the location where the InvoiceProcessing solution has been saved to and import the solution.</li>
    </ol>
    <li>Once the Invoice solution has been uploaded configure the environment variables:</li>
    <ol>
    <li>Create a new connection to the SharePoint site collection/list for the Invoices and Invoice Line Items list.</li>
    <li>Navigate to the imported solution "Invoice Processing" and edit each of the Environment variables to your environment:</li>
        <ul>
            <li>FormsRecognizerURL - In the Azure resource group that was created, choose the InvoiceAutomationFormsRecognizer CognitiveServices type we created above.  In the overview section, copy the Endpoint and use that as the value in the environment variable. (Example:  <https://invoiceautomationformrecognizer.cognitiveservices.azure.com/></li>
![Forms Recognizer Environment Variable](images/7-FormsRecognizerURL.png)
<P><br>

![Forms Recognizer Environment Variable](images/7-FormsRecognizerURL2.png)
</p>
            <li>Ocp-Apim-Subscription-Key - in the Keys and Endpoints blade copy one of the keys and use it in this environment variable. (Example:  e3b066e2ee454c2ebb198005...)</li>

![Ocp-Apim](images/8-OcpApim.png)
            <li>InvoiceLineItemsAzureFunction- The URL from the function app that was created in Azure.  (Example:  <https://invoicelineitems.azurewebsites.net/>)</li>

![Line items Azure Function](images/9-InvoiceLineItemsAzureFunction.png)  
            <li>InvoiceSiteCollection - the site collection in your tenant where the Invoices library was created (format:  /sites/<SiteCollection>)</li>
            <li>SiteCollection - update the connection with the site collection the invoices library was created in.</li>
        </ul>
    </ol>
</ol>

## Test the solution

Once all the assets have been deployed and the configurations have been applied to your environment you can test the solution by first uploading a document into the Invoices document library and monitoring the Power Automate workflow.  Errors may need to be remediated depending on your environment configuration.

Once this has ran successfully, open the PowerApp and view the document that has been uploaded.
