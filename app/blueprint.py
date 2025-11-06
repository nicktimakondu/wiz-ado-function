# This file defines the Azure Function trigger using a Blueprint for the v2 Python model.

import azure.functions as func
import logging

from webhook_logic import handle_webhook_request # Ensure this path is correct for your project structure

devops_webhook_bp = func.Blueprint()

@devops_webhook_bp.function_name("WriteToADO")
@devops_webhook_bp.route(route="webhook-to-devops", auth_level=func.AuthLevel.FUNCTION, methods=[func.HttpMethod.POST])
def webhook_to_devops_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function (v2 model with blueprint) processed a request.")
    return handle_webhook_request(req)