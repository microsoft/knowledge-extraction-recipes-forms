provider "azurerm" {
  features {
  }
}

resource "azurerm_resource_group" "rg" {
  name     = var.region
  location = var.location
}

resource "azurerm_container_group" "form-v1" {
  name                = "${var.prefix}-fr-v1"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  ip_address_type     = "public"
  os_type             = "linux"
  dns_name_label      = "${var.prefix}-fr-v1"

  image_registry_credential {
    server   = var.registry
    username = var.user
    password = var.password
  }

  container {
    name   = "fr"
    image  = "${var.registry}/microsoft/cognitive-services-form-recognizer:latest"
    cpu    = "2"
    memory = "5"

    ports {
      port     = 80
      protocol = "TCP"
    }

    environment_variables = {
      "Kestrel__Endpoints__Http__Url"                    = "http://0.0.0.0:80"      
      "eula"                                             = "accept"
      "billing"                                          = var.billingEndpoint
      "apikey"                                           = var.formRecognizerApiKey
      "FormRecognizer__ComputerVisionApiKey"             = var.computerVisionApiKey
      "FormRecognizer__ComputerVisionEndpointUri"        = "http://localhost:4000"
      "FormRecognizer__SyncProcessTaskCancelLimitInSecs" = 300
    }

    volume {
      name                 = "in"
      mount_path           = "/input"
      storage_account_name = var.storageAccountName
      storage_account_key  = var.storageAccountKey
      share_name           = var.inputShare
    }

    volume {
      name                 = "out"
      mount_path           = "/output"
      storage_account_name = var.storageAccountName
      storage_account_key  = var.storageAccountKey
      share_name           = var.outputShare
    }
  }

  container {
    name   = "cv"
    image  = "${var.registry}/microsoft/cognitive-services-recognize-text:latest"
    cpu    = "2"
    memory = "8"

    ports {
      port     = 4000
      protocol = "TCP"
    }

    environment_variables = {
      "ASPNETCORE_URLS" = "http://0.0.0.0:4000"
      "eula"            = "accept"
      "billing"         = var.cognitive_services_endpoint
      "apikey"          = var.computerVisionApiKey
    }
  }
}