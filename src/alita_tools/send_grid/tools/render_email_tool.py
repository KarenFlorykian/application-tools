import logging
import traceback
from typing import Dict, Any, Type
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field, create_model, ValidationError
from ..api_wrapper import SendGridAPIWrapper

logger = logging.getLogger(__name__)

class RenderEmailTemplateTool(BaseTool):
    """
    Render a Jinja2 email template with the required context data.
    Potentially checks for known templates (like 'gatling_report.html') and 
    ensures the context has required fields.
    """
    name: str = "render_email_template"
    description: str = "Render a template (like gatling_report.html, weekly_report.html) with context data"
    api_wrapper: SendGridAPIWrapper = Field(..., description="API Wrapper used to find & render the template")

    args_schema: Type[BaseModel] = create_model(
        "RenderEmailTemplateArgs",
        template_name=(str, Field(..., description="Which template file to use. E.g. 'gatling_report.html'")),
        context_data=(Dict[str, Any], Field(default={}, description="Data to populate in the template"))
    )

    def _run(self, template_name: str, context_data: Dict[str, Any] = None) -> str:
        """
        Render the template. If context_data is missing, we use an empty dict by default.
        """
        # Potentially do specialized validation
        # If template_name is 'gatling_report.html', check for 't_params', 'summary', etc.
        # If template_name is 'weekly_report.html', check for 'engagement', 'tickets_summary', ...
        context_data = context_data or {}

        try:
            logger.info(f"Rendering template: {template_name}")
            return self.api_wrapper.render_template(template_name, context_data)
        except Exception as e:
            stacktrace = traceback.format_exc()
            logger.error(f"Template rendering error: {stacktrace}")
            raise ToolException(f"Failed to render email template: {str(e)}")

__all__ = [
    {"name": "render_email_template", "tool": RenderEmailTemplateTool}
]