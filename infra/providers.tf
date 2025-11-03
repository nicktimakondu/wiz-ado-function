terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>4.50"
    }
  }

  backend "azurerm" {
    
  }
}


# Configure the Azure Provider
provider "azurerm" {
  features {}
}

# terraform init -reconfigure -backend-config="storage_account_name=ntimakondutfstate1" -backend-config="container_name=tfstate" -backend-config="key=terraform.state" -backend-config="resource_group_name=nt-rg"