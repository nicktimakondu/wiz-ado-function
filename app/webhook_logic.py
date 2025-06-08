# webhook_logic.py
# This file contains the core logic for processing the webhook and creating a work item.

import logging
import json
import os
import requests
# import msal # No longer directly used for token acquisition
import azure.functions as func
from azure.identity import DefaultAzureCredential, ChainedTokenCredential, ManagedIdentityCredential, EnvironmentCredential
from azure.core.exceptions import ClientAuthenticationError

# Configuration - Retrieve from Application Settings / Environment Variables
# These are still useful as DefaultAzureCredential can pick them up (EnvironmentCredential)
# or for other potential configurations.
TENANT_ID = os.environ.get("AZURE_TENANT_ID")
CLIENT_ID = os.environ.get("AZURE_CLIENT_ID") # Used by DefaultAzureCredential (EnvironmentCredential) if set
# CLIENT_SECRET is also used by EnvironmentCredential if set

DEVOPS_ORG_URL = os.environ.get("DEVOPS_ORG_URL")  # e.g., "https://dev.azure.com/YourOrganizationName"
DEVOPS_PROJECT = os.environ.get("DEVOPS_PROJECT_NAME")
DEFAULT_WORK_ITEM_TYPE = os.environ.get("DEFAULT_WORK_ITEM_TYPE", "Task") # Default if not in webhook

# Azure DevOps API details
DEVOPS_API_VERSION = "7.2-preview"
DEVOPS_RESOURCE_ID = "499b84ac-1321-427f-aa17-267ca6975798" # Static Azure DevOps resource ID
DEVOPS_SCOPE = f"{DEVOPS_RESOURCE_ID}/.default" # Scope for Azure AD V2 endpoint

# Helper function to acquire Azure DevOps access token using DefaultAzureCredential
def get_devops_access_token():
    """
    Acquires an access token for Azure DevOps API using DefaultAzureCredential.
    DefaultAzureCredential attempts multiple credential types in a chain,
    including EnvironmentCredential (reads AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET),
    ManagedIdentityCredential (for Azure-hosted services with Managed Identity),
    AzureCliCredential, etc.
    """
    try:
        # For Azure Functions with Managed Identity, ensure the identity has permissions to Azure DevOps.
        # If running locally and AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID are set,
        # EnvironmentCredential within DefaultAzureCredential will use them.
        
        # You can be more explicit if needed:
        # credential = ChainedTokenCredential(
        #     ManagedIdentityCredential(client_id=CLIENT_ID if CLIENT_ID else None), # Use specific user-assigned MI if CLIENT_ID is its ID
        #     EnvironmentCredential()
        # )
        # However, DefaultAzureCredential is often sufficient.
        credential = DefaultAzureCredential()
        
        logging.info(f"Attempting to get token for scope: {DEVOPS_SCOPE}")
        access_token_info = credential.get_token(DEVOPS_SCOPE)
        logging.info("Successfully acquired Azure DevOps access token using DefaultAzureCredential.")
        return access_token_info.token
    except ClientAuthenticationError as e:
        logging.error(f"Failed to acquire Azure DevOps access token using DefaultAzureCredential (ClientAuthenticationError).")
        logging.error(f"Error: {e}")
        # Log more details if available, e.g., e.message or specific attributes of the error
        # Check if the Function App has a Managed Identity configured and if it has the necessary permissions on Azure DevOps.
        # If running locally, check environment variables (AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET) or Azure CLI login.
        return None
    except Exception as e:
        # Catch any other exceptions during token acquisition
        logging.error(f"An unexpected error occurred while acquiring Azure DevOps access token: {e}")
        return None

# Core logic function, called by the trigger defined in blueprint.py
def handle_webhook_request(req: func.HttpRequest) -> func.HttpResponse:
    """
    Processes an incoming webhook request, authenticates with Azure DevOps,
    and creates a work item based on the webhook payload.
    """
    # 1. Get Azure DevOps Access Token
    access_token = get_devops_access_token()
    if not access_token:
        return func.HttpResponse(
             "Failed to authenticate with Azure DevOps. Check function logs for details. Ensure Managed Identity (if applicable) or local credentials are correctly configured and have permissions.",
             status_code=500
        )

    # 2. Parse Incoming Webhook Data
    try:
        req_body = req.get_json()
    except ValueError:
        logging.error("Invalid JSON received in webhook request body.")
        return func.HttpResponse(
             "Please pass a valid JSON object in the request body",
             status_code=400
        )
    
    control_data = req_body.get("control")
    if not control_data or not isinstance(control_data, dict):
        logging.error("Webhook payload must contain an 'control' object.")
        return func.HttpResponse(
             "Webhook payload must contain an 'control' object.",
             status_code=400
        )

    title = control_data.get("name") 
    if not title:
        logging.error("Webhook payload's 'control' object must contain an 'name' field to be used as the work item title.")
        return func.HttpResponse(
             "Webhook payload's 'control' object must contain an 'name' field for the work item title.",
             status_code=400
        )

    try:
        description_content = json.dumps(req_body, indent=2)
        description_html = f"<p>Raw Webhook Payload:</p><pre>{description_content}</pre>"
    except Exception as e:
        logging.error(f"Error formatting JSON for description: {e}")
        description_html = "<p>Error formatting webhook payload for description. Check logs.</p>"

    work_item_type_from_payload = req_body.get("workItemType", DEFAULT_WORK_ITEM_TYPE) 

    if not DEVOPS_ORG_URL or not DEVOPS_PROJECT:
        logging.error("DEVOPS_ORG_URL or DEVOPS_PROJECT_NAME is not configured.")
        return func.HttpResponse(
            "Azure DevOps organization URL or project name is not configured in function settings.",
            status_code=500
        )

    # 3. Construct Work Item Payload (JSON Patch document)
    patch_document = [
        {
            "op": "add",
            "path": "/fields/System.Title",
            "value": f'Wiz - {str(title)}'
        },
        {
            "op": "add",
            "path": "/fields/System.Description",
            "value": description_html
        }
        # Add other fields as needed
    ]

    # 4. Create Work Item using Azure DevOps API
    create_work_item_url = f"{DEVOPS_ORG_URL}/{DEVOPS_PROJECT}/_apis/wit/workitems/${work_item_type_from_payload}?api-version={DEVOPS_API_VERSION}"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json-patch+json"
    }

    try:
        response = requests.post(create_work_item_url, data=json.dumps(patch_document), headers=headers)
        response.raise_for_status() 

        work_item_info = response.json()
        logging.info(f"Successfully created work item ID: {work_item_info['id']} in project {DEVOPS_PROJECT}.")
        return func.HttpResponse(
            json.dumps({"message": "Work item created successfully", "workItemId": work_item_info['id'], "url": work_item_info['_links']['html']['href']}),
            status_code=201, 
            mimetype="application/json"
        )

    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        logging.error(f"Response content: {response.text}")
        return func.HttpResponse(
             f"Failed to create work item. Azure DevOps API Error: {response.text}",
             status_code=response.status_code
        )
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return func.HttpResponse(
             "An unexpected error occurred while creating the work item.",
             status_code=500
        )
