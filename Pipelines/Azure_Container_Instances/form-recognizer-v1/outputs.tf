output "form_recognizer_v1_endpoint" {
  value = azurerm_container_group.form-v1.fqdn
}

output "swagger_endpoint" {
  value = "${azurerm_container_group.form-v1.fqdn}/swagger"
}

output "api_status" {
  value = "${azurerm_container_group.form-v1.fqdn}/status"
}