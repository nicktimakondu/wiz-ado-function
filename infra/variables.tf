variable "resource_group_name" {
  description = "The name of the resource group."
  type        = string
  default     = "rg-webhook-function"
}

variable "location" {
  description = "The Azure region where resources will be created."
  type        = string
  default     = "Central US"
}

variable "storage_account_name" {
  description = "A unique name for the storage account (lowercase letters and numbers only). A random suffix will be added."
  type        = string
  default     = "wizwebhookfunc" # Must be globally unique
}

variable "app_service_plan_name" {
  description = "The name of the App Service Plan."
  type        = string
  default     = "plan-webhook-function-002"
}

variable "function_app_name" {
  description = "A unique name for the Function App."
  type        = string
  default     = "wiz-webhook-to-devops-002" # Must be globally unique
}

variable "devops_org_url" {
  description = "The URL of the Azure DevOps organization (e.g., https://dev.azure.com/YourOrgName)."
  type        = string
  sensitive   = true # Mark as sensitive as it might contain identifying info
}

variable "devops_project_name" {
  description = "The name of the Azure DevOps project."
  type        = string
}