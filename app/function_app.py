# This file is the entry point for your Azure Functions app using the v2 Python model.
# It should be at the root of your Function App project.

import azure.functions as func
from blueprint import devops_webhook_bp # Ensure this path is correct

app = func.FunctionApp() 
app.register_functions(devops_webhook_bp)
