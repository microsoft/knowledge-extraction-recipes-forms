output "storage-connection-string" {
  value = "${azurerm_storage_account.files.primary_connection_string}"
}

output "storage-container" {
  value = "${azurerm_storage_container.pdf.name}"
}

output "azure-search-url" {
  value = "https://${azurerm_search_service.cases.name}.search.windows.net"
}

output "azure-search-service-name" {
  value = "${azurerm_search_service.cases.name}"
}

output "azure-search-key" {
  value = "${azurerm_search_service.cases.primary_key}"
}

output "cognitive-service-id" {
  value = "${azurerm_cognitive_account.cognitive-account.id}"
}

output "cognitive-service-key" {
  value = "${azurerm_cognitive_account.cognitive-account.primary_access_key}"
}
