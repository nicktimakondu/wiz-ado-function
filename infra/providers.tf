terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>4.0"
    }
  }

  backend "azurerm" {
    
  }
}


# Configure the Azure Provider
provider "azurerm" {
  features {}
}

# terraform init -backend-config="storage_account_name=ntimakondutfstate" -backend-config="container_name=tfstate" -backend-config="key=terraform.state" -backend-config="resource_group_name=DefaultResourceGroup-EUS2"