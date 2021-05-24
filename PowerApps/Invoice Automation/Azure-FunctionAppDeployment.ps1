
$location = "East US"
$resourceGroupName = "InvoiceAutomation"
$storageAccountName = "invoicenautomationrg"
$functionName = "InvoiceLineItems"
$sourceZipPath = "<SourceZipPath>\InvoiceLineItems.zip"

Connect-AzAccount

New-AzStorageAccount -ResourceGroupName $resourceGroupName -Name $storageAccountName -Location $location -SkuName "Standard_LRS"
New-AzFunctionApp -Name $functionName -StorageAccountName $storageAccountName -Location $location -ResourceGroupName $resourceGroupName -FunctionsVersion 2 -Runtime DotNet

Publish-AzWebapp -ResourceGroupName $resourceGroupName -Name $functionName -ArchivePath $sourceZipPath
