import logging
from functools import lru_cache
from typing import Dict, List, Optional, Literal

from langchain_core.tools import BaseToolkit, BaseTool
from pydantic import BaseModel, Field, ConfigDict, create_model, model_validator

from .api_wrapper import SendGridAPIWrapper
from .tools import __all__ as available_tools

logger = logging.getLogger(__name__)
name = "SendGrid"


class AlitaSendGridToolkit(BaseToolkit):
    """
    SendGrid Email Toolkit for Elitea/Alita SDK.
    Provides tools for sending emails, converting Markdown, rendering templates, etc.
    """
    tools: List[BaseTool] = []
    toolkit_max_length: int = 100

    @classmethod
    @lru_cache(maxsize=32)
    def toolkit_config_schema(cls) -> BaseModel:
        selected_tools = {}
        for t in available_tools:
            default = t['tool'].__pydantic_fields__['args_schema'].default
            selected_tools[t['name']] = default.schema() if default else default
        #cls.toolkit_max_length = get_max_toolkit_length(selected_tools)
        return create_model(
            name,
            api_key=(str, Field(..., description=f"{name} API Key", json_schema_extra={"secret": True})),
            default_from_email=(str, Field(..., description="Default sender email address")),
            default_from_name=(Optional[str], Field(None, description="Default sender name")),
            selected_tools=(List[str], Field(default=[], description="Tools to activate. Empty means all.")),
            __config__=ConfigDict(
                json_schema_extra={
                    "metadata": {
                        "label": name,
                        "version": "1.0.0",
                        "capabilities": {
                            "tool_names": selected_tools
                        }
                    }
                }
            )
        )

        @model_validator(mode="before")
        def validate_input(cls, values):
            if not values.get("api_key"):
                raise ValueError("SendGrid API Key is required.")
            if "@" not in values.get("default_from_email", ""):
                raise ValueError("default_from_email must be a valid email.")
            return values

        SendGrid.__validators__ = [validate_input]
        return SendGrid

    @classmethod
    def get_toolkit(
            cls,
            api_key: str,
            default_from_email: str,
            default_from_name: Optional[str] = None,
            selected_tools: Optional[List[str]] = None,
            toolkit_name: Optional[str] = None
    ) -> "AlitaSendGridToolkit":
        selected_tools = selected_tools or []

        # Build the API wrapper
        api_wrapper = SendGridAPIWrapper(
            api_key=api_key,
            default_from_email=default_from_email,
            default_from_name=default_from_name
        )

        tool_objs = []
        for tool_def in available_tools:
            tool_name = tool_def["name"]
            if not selected_tools or tool_name in selected_tools:
                tool_class = tool_def["tool"]
                # Check if the class requires 'api_wrapper'
                if "api_wrapper" in tool_class.__pydantic_fields__:
                    instance = tool_class(api_wrapper=api_wrapper)
                else:
                    instance = tool_class()

                if toolkit_name:
                    instance.name = f"{toolkit_name}_{instance.name}"

                tool_objs.append(instance)

        return cls(tools=tool_objs)

    def get_tools(self) -> List[BaseTool]:
        logger.info(f"[AlitaSendGridToolkit] Retrieving {len(self.tools)} initialized tools")
        return self.tools

# Simplified utility method for toolkit retrieval
def get_tools(tool_config: Dict) -> List[BaseTool]:
    return AlitaSendGridToolkit.get_toolkit(
        selected_tools=tool_config.get('selected_tools', []),
        api_key=tool_config['settings']['api_key'],
        default_from_email=tool_config['settings'].get('from_email'),
        default_from_name=tool_config['settings']['from_name'],
        toolkit_name=tool_config.get('toolkit_name')
    ).get_tools()