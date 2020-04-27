variable "prefix" {
  description = "Prefix for resource creation"
}

variable "region" {
  description = "Resource group to use"
}

variable "location" {
  description = "Azure data center location"
  default = "West Europe"
}

variable "registry" {
  description = "Container registry to use "
  default = "containerpreview.azurecr.io"
}

variable "cognitive_services_endpoint" {
  description = "Cognitive services billing url"
  default = "https://westeurope.api.cognitive.microsoft.com/"
}

variable "user" {
  description = "Container registry user"
}

variable "password" {
  description = "Container registry user password"
}

variable "billingEndpoint" {
  description = "Form recognizer billing endpoint url"
}

variable "formRecognizerApiKey" {
  description = "Form recognizer api key"
}

variable "computerVisionApiKey" {
  description = "Computer vision api key"
}

variable "storageAccountName" {
  description = "Storage account to use for Azure File Shares"
}

variable "storageAccountKey" {
  description = "Storage account key"
}

variable "inputShare" {
  description = "File share name for the input endpoint for Form Recognizer"
  default = "form-recognizer-v1-input"
}

variable "outputShare" {
  description = "File share name for the output endpoint for Form Recognizer"
  default = "form-recognizer-v1-output"
}


