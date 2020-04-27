variable "location" {
  type        = "string"
  description = "Azure location you will deploy the infrastructure"
  default     = "East US 2"
}

variable "resource_group" {
  type        = "string"
  description = "Azure resource group name"
  default     = "CasesRGDemo"
}

variable "storage_container_name" {
  type        = "string"
  description = "Storage container name to store PDF/Images documents"
  default     = "pdf"
}
