import logging
import traceback
import json
from typing import Dict, Any, List, Type, Optional
from langchain_core.tools import BaseTool, ToolException
from pydantic.fields import Field
from pydantic import BaseModel, create_model
from ..api_wrapper import SendGridAPIWrapper

logger = logging.getLogger(__name__)


class SelectEmailTemplateTool(BaseTool):
    """
    Tool that lists known templates and optionally returns the chosen template name.

    Provides user-friendly guidance if no templates exist or the user doesn't specify
    what to do (list or choose).
    """
    name: str = "select_email_template"
    description: str = (
        "List or pick one of the existing email templates (e.g. gatling_report.html, weekly_report.html). "
        "If no templates are found, returns a helpful message."
    )
    api_wrapper: SendGridAPIWrapper = Field(..., description="API Wrapper used to list templates")

    # By default we expect either action='list' or action='choose' + template_name
    args_schema: Type[BaseModel] = create_model(
        "SelectTemplateArgs",
        action=(str, Field(
            default="list",
            description="Specify 'list' to see all templates, or 'choose' to pick one"
        )),
        template_name=(Optional[str], Field(
            None,
            description="If action='choose', provide the exact template filename to select"
        ))
    )

    def _run(self, action: str = "list", template_name: Optional[str] = None) -> str:
        """
        Execute the tool logic. 'list' action shows available templates, 
        'choose' attempts to confirm a specific template.
        """
        try:
            # 1) If user wants to list templates
            if action.lower() == "list":
                templates = self.api_wrapper.list_templates()
                if not templates:
                    return (
                        "⚠️ No email templates found in the default directory.\n"
                        "You can add templates (e.g. 'gatling_report.html', 'weekly_report.html') "
                        "to the folder or specify a different directory if needed."
                    )
                # Present them in a user-friendly JSON block
                return (
                        "Here are the available templates:\n" +
                        json.dumps(templates, indent=2) +
                        "\nUse action='choose' plus one of these filenames in 'template_name' to pick one."
                )

            # 2) If user wants to choose a specific template
            elif action.lower() == "choose":
                if not template_name:
                    return (
                        "⚠️ You chose 'choose' action but didn't specify a 'template_name'.\n"
                        "Use template_name='...' with a known filename from the 'list' output."
                    )

                # Validate template_name
                templates = self.api_wrapper.list_templates()
                if not templates:
                    return (
                        "⚠️ No templates found at all. You cannot 'choose' a template. "
                        "Please add template files or specify a correct directory first."
                    )

                if template_name not in templates:
                    return (
                        f"⚠️ Template '{template_name}' was not found in the directory.\n"
                        f"Available templates:\n{json.dumps(templates, indent=2)}"
                    )

                # If found
                return (
                    f"✅ Template '{template_name}' is valid.\n"
                    "You can now pass it to 'render_email_template' with appropriate context data."
                )

            else:
                # 3) Unknown action
                return (
                    f"⚠️ Unknown action '{action}'.\n"
                    "Please use 'list' to see available templates, or 'choose' with 'template_name' to pick one."
                )
        except Exception as e:
            stacktrace = traceback.format_exc()
            logger.error(f"Select email template error: {stacktrace}")
            raise ToolException(str(e))


__all__ = [
    {"name": "select_email_template", "tool": SelectEmailTemplateTool}
]