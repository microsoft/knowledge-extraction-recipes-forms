resource "random_id" "random" {
  byte_length = 4
}

resource "azurerm_resource_group" "cases" {
  name     = "${var.resource_group}"
  location = "${var.location}"
}

resource "azurerm_search_service" "cases" {
  name                = "casessearch${lower(random_id.random.hex)}"
  resource_group_name = "${azurerm_resource_group.cases.name}"
  location            = "${azurerm_resource_group.cases.location}"
  sku                 = "standard"
  replica_count       = 1
  partition_count     = 1
}

resource "azurerm_storage_account" "files" {
  name                     = "casesfiles${lower(random_id.random.hex)}"
  resource_group_name      = "${azurerm_resource_group.cases.name}"
  location                 = "${azurerm_resource_group.cases.location}"
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_container" "pdf" {
  name                  = "${var.storage_container_name}"
  storage_account_name  = "${azurerm_storage_account.files.name}"
  container_access_type = "private"
}

resource "azurerm_cognitive_account" "cognitive-account" {
  name                = "cognitiveaccount${lower(random_id.random.hex)}"
  location            = "${azurerm_resource_group.cases.location}"
  resource_group_name = "${azurerm_resource_group.cases.name}"
  kind                = "CognitiveServices"

  sku {
    name = "S0"
    tier = "Standard"
  }
}
