import logging
import traceback
import json
from typing import Type
from langchain_core.tools import BaseTool, ToolException
from pydantic.fields import Field
from ..api_wrapper import SendGridAPIWrapper

logger = logging.getLogger(__name__)

class ListEmailTemplatesTool(BaseTool):
    """
    Tool for listing available email templates in the configured template directory.
    """
    name: str = "list_email_templates"
    description: str = "List all available email templates"
    api_wrapper: SendGridAPIWrapper = Field(..., description="SendGrid API Wrapper instance")

    def _run(self):
        try:
            logger.info("Listing available templates")
            templates = self.api_wrapper.list_templates()
            if not templates:
                return "No email templates found"
            return json.dumps(templates, indent=2)
        except Exception as e:
            stacktrace = traceback.format_exc()
            logger.error(f"List templates error: {stacktrace}")
            raise ToolException(str(e))

__all__ = [
    {"name": "list_email_templates", "tool": ListEmailTemplatesTool}
]