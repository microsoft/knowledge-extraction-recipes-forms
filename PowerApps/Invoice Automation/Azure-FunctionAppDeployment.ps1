#http://www.redbaronofazure.com/?cat=428
#https://demiliani.com/2020/03/26/a-quick-way-to-deploy-your-azure-functions-in-the-cloud/


$location = "East US"
$resourceGroupName = "InvoiceAutomation"
$storageAccountName = "invoicenautomationrg"
$functionName = "InvoiceLineItems"
$sourceZipPath = "C:\Users\stpuceli\source\repos\HelloWorld\bin\Release\netcoreapp3.0\publish\InvoiceLineItems.zip"

#Install-Module AzureRM -AllowClobber
#Import-Module AzureRM

#Then issue command:


Connect-AzAccount

#New-AzStorageAccount -ResourceGroupName $resourceGroupName -Name $storageAccountName -Location $location -SkuName "Standard_LRS"


#New-AzFunctionApp -Name $functionName -StorageAccountName $storageAccountName -Location $location -ResourceGroupName $resourceGroupName -FunctionsVersion 2 -Runtime DotNet

Publish-AzWebapp -ResourceGroupName $resourceGroupName -Name $functionName -ArchivePath $sourceZipPath

New-AzureRmResource -ResourceGroupName $resourceGroupName -ResourceType "Microsoft.Web/Sites" -ResourceName $functionName -kind "functionapp" -Location $location -Properties @{} -force


az functionapp create --name $functionName --storage-account $storageAccountName --consumption-plan-location "East US" --resource-group $resourceGroupName --functions-version 2



az webapp deployment source config-zip -g $resourceGroupName -n $functionName --src $sourceZipPath