import logging
import traceback
from typing import Type
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field, create_model
import markdown

logger = logging.getLogger(__name__)

class ConvertMarkdownToHtmlTool(BaseTool):
    """
    Tool for converting Markdown content to HTML.
    """
    name: str = "convert_markdown_to_html"
    description: str = "Convert Markdown text to HTML for email formatting."

    args_schema: Type[BaseModel] = create_model(
        "ConvertMarkdownArgs",
        markdown_content=(str, Field(..., description="Markdown content to convert")),
        enable_extensions=(bool, Field(default=True, description="Enable Markdown extensions like tables, code"))
    )

    def _run(self, markdown_content: str, enable_extensions: bool = True) -> str:
        try:
            logger.info("Converting Markdown to HTML")
            extensions = ["tables", "fenced_code"] if enable_extensions else []
            html_content = markdown.markdown(markdown_content, extensions=extensions)
            return html_content
        except Exception as e:
            stacktrace = traceback.format_exc()
            logger.error(f"Markdown conversion error: {stacktrace}")
            raise ToolException(f"Failed to convert Markdown to HTML: {str(e)}")

__all__ = [
    {"name": "convert_markdown_to_html", "tool": ConvertMarkdownToHtmlTool}
]