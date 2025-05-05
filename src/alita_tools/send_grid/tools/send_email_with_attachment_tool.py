import logging
import traceback
from typing import Type, Dict, List
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field, create_model

from ..api_wrapper import SendGridAPIWrapper

logger = logging.getLogger(__name__)

class SendEmailWithAttachmentTool(BaseTool):
    """
    Tool for sending an email with attachments via SendGrid.
    """
    name: str = "send_email_with_attachment"
    description: str = "Send an email with file attachments (base64) via SendGrid."
    api_wrapper: SendGridAPIWrapper = Field(..., description="SendGrid API Wrapper instance")

    args_schema: Type[BaseModel] = create_model(
        "SendEmailWithAttachmentArgs",
        subject=(str, Field(..., description="Email subject line")),
        body=(str, Field(..., description="Email body (HTML or plain text)")),
        recipients=(List[str], Field(..., description="List of recipient email addresses")),
        attachments=(List[Dict[str, str]], Field(default=[], description="List of attachment dicts")),
        is_html=(bool, Field(default=True, description="Whether body is HTML (True) or plain text (False)"))
    )

    def _run(
        self,
        subject: str,
        body: str,
        recipients: List[str],
        attachments: List[Dict[str, str]],
        is_html: bool
    ) -> str:
        try:
            logger.info(f"Sending email with {len(attachments)} attachment(s) to {len(recipients)} recipient(s)")
            result = self.api_wrapper.send_email(
                subject=subject,
                body=body,
                recipients=recipients,
                is_html=is_html,
                attachments=attachments
            )
            if result["success"]:
                attachment_names = [a.get("filename", "unnamed") for a in attachments]
                return f"✅ Email with attachment(s) {', '.join(attachment_names)} sent successfully!"
            else:
                raise ToolException(f"Failed to send email: {result.get('body')}")
        except Exception as e:
            stacktrace = traceback.format_exc()
            logger.error(f"Send email with attachment error: {stacktrace}")
            raise ToolException(str(e))

__all__ = [
    {"name": "send_email_with_attachment", "tool": SendEmailWithAttachmentTool}
]