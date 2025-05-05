import logging
import traceback
from typing import Type, List, Dict, Any, Optional
from langchain_core.tools import BaseTool, ToolException
from pydantic.fields import Field
from pydantic import BaseModel, create_model

from ..api_wrapper import SendGridAPIWrapper

logger = logging.getLogger(__name__)


class SendEmailTool(BaseTool):
    """
    Smart email sending tool that checks domain, distribution size, 
    large attachments, and user confirmation hints.
    """
    name: str = "send_email"
    description: str = (
        "Send an email with subject, body, recipients, attachments, etc. "
        "If the distribution list is large or suspicious domains are found, it returns a warning."
    )
    api_wrapper: SendGridAPIWrapper = Field(..., description="SendGrid API wrapper instance")

    args_schema: Type[BaseModel] = create_model(
        "SendEmailArgs",
        subject=(str, Field(default="No Subject", description="Email subject")),
        body=(str, Field(default="", description="Email body content (HTML or plain text)")),
        recipients=(List[str], Field(default=[], description="List of recipients")),
        is_html=(bool, Field(default=True, description="True if body is HTML, false for plain text")),
        attachments=(List[Dict[str, str]], Field(default=[], description="List of attachments, if any")),
        large_dist_threshold=(
        int, Field(default=5, description="If recipients exceed this, returns a user confirmation message")),
        suspicious_domains=(List[str], Field(default=["example.com"], description="Domains flagged as suspicious")),
        max_attachment_size_kb=(int, Field(default=500, description="Max size in kilobytes for each attachment"))
    )

    def _run(
            self,
            subject: str = "No Subject",
            body: str = "",
            recipients: List[str] = None,
            is_html: bool = True,
            attachments: List[Dict[str, str]] = None,
            large_dist_threshold: int = 5,
            suspicious_domains: List[str] = None,
            max_attachment_size_kb: int = 500
    ) -> str:
        recipients = recipients or []
        attachments = attachments or []
        suspicious_domains = suspicious_domains or ["example.com"]

        # 1) Check basic fields
        if not recipients:
            msg = (
                "⚠️ No recipients provided. "
                "Please provide a non-empty list of email addresses to send this email."
            )
            logger.warning(msg)
            return msg

        if not body.strip():
            msg = (
                "⚠️ The email body is empty. Provide some text or use render_email_template first. "
                "Then pass the result here as 'body'."
            )
            logger.warning(msg)
            return msg

        # 2) Check distribution size
        if len(recipients) > large_dist_threshold:
            return (
                f"🚨 You have {len(recipients)} recipients, which is above the threshold of {large_dist_threshold}. "
                "Are you sure you want to send to so many people?"
            )

        # 3) Check suspicious domains
        flagged = []
        for r in recipients:
            if "@" not in r:
                flagged.append(r + " (invalid format)")
                continue
            domain = r.split("@")[-1].lower()
            if domain in suspicious_domains:
                flagged.append(r)
        if flagged:
            return (
                f"⚠️ The following recipients look suspicious or invalid:\n{', '.join(flagged)}\n"
                "Please confirm or remove them before sending."
            )

        # 4) Check attachments for size or missing content
        for att in attachments:
            content_b64 = att.get("content", "")
            # approximate check: base64 length is about 4/3 size. 
            # This is a naive check, but good for a demo
            size_kb = len(content_b64) * 0.75 / 1024
            if size_kb > max_attachment_size_kb:
                return (
                    f"⚠️ Attachment {att.get('filename', 'unknown')} is approx {size_kb:.1f} KB, "
                    f"exceeding {max_attachment_size_kb} KB limit. "
                    "Consider removing or compressing the attachment."
                )

        # 5) If all checks pass, attempt to send
        try:
            logger.info(f"Sending email to: {', '.join(recipients)} subject='{subject}'")
            result = self.api_wrapper.send_email(
                subject=subject,
                body=body,
                recipients=recipients,
                is_html=is_html,
                attachments=attachments
            )
            if result["success"]:
                return f"✅ Email sent successfully to {', '.join(recipients)}"
            else:
                return f"⚠️ Failed to send email. Response body: {result.get('body')}"
        except Exception as e:
            stacktrace = traceback.format_exc()
            logger.error(f"Send email error: {stacktrace}")
            return f"🚨 An error occurred: {str(e)}"


__all__ = [
    {"name": "send_email", "tool": SendEmailTool}
]
