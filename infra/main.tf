# This file defines the Azure resources to be created.

# Create a resource group to hold all the resources
resource "azurerm_resource_group" "rg" {
  name     = "wiz-${var.resource_group_name}"
  location = var.location
}

# Add a random string to ensure the storage account name is unique
resource "random_string" "random" {
  length  = 4
  special = false
  upper   = false
  numeric = true
  lower   = true
}

# Create a storage account required by the Function App
resource "azurerm_storage_account" "sa" {
  name                     = "${var.storage_account_name}${random_string.random.result}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_container" "sc" {
  name                  = "${var.storage_account_name}-container"
  storage_account_id  = azurerm_storage_account.sa.id
  container_access_type = "private"
}

# Create a Linux Consumption App Service Plan
resource "azurerm_service_plan" "plan" {
  name                = var.app_service_plan_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "FC1" # Y1 is the sku for Consumption plan
}

# Create the Python Function App using the Flex Consumption resource type
resource "azurerm_function_app_flex_consumption" "func" {
  name                = var.function_app_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  service_plan_id     = azurerm_service_plan.plan.id

  storage_container_type      = "blobContainer"
  storage_container_endpoint  = "${azurerm_storage_account.sa.primary_blob_endpoint}${azurerm_storage_container.sc.name}"
  storage_authentication_type = "StorageAccountConnectionString"
  storage_access_key          = azurerm_storage_account.sa.primary_access_key

  runtime_name    = "python"
  runtime_version = "3.11"

  # Enable the system-assigned managed identity
  identity {
    type = "SystemAssigned"
  }

  maximum_instance_count = 50
  instance_memory_in_mb  = 2048

  site_config {}

  # Application settings required for the function
  app_settings = {
    "PYTHON_ENABLE_WORKER_EXTENSIONS" = "1", # Required for the v2 Python model
    "DEVOPS_ORG_URL"                  = var.devops_org_url,
    "DEVOPS_PROJECT_NAME"             = var.devops_project_name,
    "DEFAULT_WORK_ITEM_TYPE"          = "Task"
    # NOTE: We are NOT setting TENANT_ID, CLIENT_ID, or CLIENT_SECRET here.
    # The function will use the System-Assigned Managed Identity.
  }

  tags = {
    "Project" = "WebhookToDevOps"
  }

  depends_on = [
    azurerm_service_plan.plan,
    azurerm_storage_account.sa,
  ]
}