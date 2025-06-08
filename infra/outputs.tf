# This file defines the output values from the Terraform configuration.

output "function_app_name" {
  description = "The name of the created Function App."
  value       = azurerm_function_app_flex_consumption.func.name
}

output "function_app_hostname" {
  description = "The hostname of the Function App."
  value       = azurerm_function_app_flex_consumption.func.default_hostname
}

output "function_app_principal_id" {
  description = "The principal ID of the Function App's system-assigned managed identity."
  value       = azurerm_function_app_flex_consumption.func.identity[0].principal_id
}
