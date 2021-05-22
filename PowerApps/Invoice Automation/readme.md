<h1>Invoice Automation using the Power Platform</h1>

Invoice processing is something that every company does, but many are still doing it manually and is very labor intensive.  Not anymore!  This starter kit is intended to use the new "Process and save information from invoices" flow in Power Automate to automatically capture invoice information, save it to a SharePoint document library.  We’ll then use Cognitive Services to extract the invoice line-item information and save it to a SharePoint List.  Finally, Power Apps will allow you to review and complete the processing so it can be integrated with the accounting LOB application.

For an overview of the solution please refer to this [blog article]("https://powerusers.microsoft.com/t5/Power-Automate-Community-Blog/Invoice-Automation-using-the-Power-Platform/ba-p/875628) for details.

<h2>Installation Process</h2>
There are several components and dependencies that comprise the solution and need to be configured to successfully deploy it in your environnement.

<h3>SharePoint Configuration</h3>
<ol>
    <li>
        Create the Invoice content type in the SharePoint admin center or at the site collection level using the following schema.       
    [![SharePoint Schema](/PowerApps/Invoice%20Automation/images/1-InvoicesContentType.png) 
    </li>
    
</ol>