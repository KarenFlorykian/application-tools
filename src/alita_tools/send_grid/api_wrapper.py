# sendgrid_api_wrapper.py
import os
import logging
from typing import Dict, Any, List, Optional
import sendgrid
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName
from sendgrid.helpers.mail import FileType, Disposition, ContentId
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)


class SendGridAPIWrapper:
    """
    Wrapper for SendGrid API operations with enhanced error handling.
    """

    DEFAULT_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

    def __init__(
            self,
            api_key: str,
            default_from_email: str,
            default_from_name: Optional[str] = None,
            template_dir: Optional[str] = None
    ):
        """
        Initialize the SendGrid API wrapper.

        :param api_key: SendGrid API key
        :param default_from_email: Default sender email address
        :param default_from_name: Default sender name
        :param template_dir: Directory containing Jinja2 email templates (defaults to ./templates if not provided)
        """
        self.api_key = api_key
        self.default_from_email = default_from_email
        self.default_from_name = default_from_name

        # Initialize SendGrid client
        self.client = sendgrid.SendGridAPIClient(api_key=api_key)
        
        # If user didn't specify a template dir, use the default
        if template_dir:
            self.template_dir = template_dir
        else:
            self.template_dir = self.DEFAULT_TEMPLATE_DIR

        # If directory doesn't exist, we can create or just log
        if not os.path.isdir(self.template_dir):
            logger.warning(f"Template directory not found: {self.template_dir}")

        # Set up Jinja environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(["html", "xml"])
        )

    def send_email(
            self,
            subject: str,
            body: str,
            recipients: List[str],
            from_email: Optional[str] = None,
            from_name: Optional[str] = None,
            is_html: bool = True,
            attachments: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Send an email using SendGrid.

        :param subject: Email subject
        :param body: Email body content
        :param recipients: List of recipient email addresses
        :param from_email: Sender email (fallback to default_from_email if None)
        :param from_name: Sender name (fallback to default_from_name if None)
        :param is_html: Whether the 'body' is HTML or plain text
        :param attachments: Optional list of attachments
        :return: Dict containing status_code, body, headers, and success flag
        """
        logger.info(f"Preparing to send email to {len(recipients)} recipient(s)")

        sender_email = from_email or self.default_from_email
        sender_name = from_name or self.default_from_name

        # Construct from_email for SendGrid
        if sender_name:
            complete_from = f"{sender_name} <{sender_email}>"
        else:
            complete_from = sender_email

        message = Mail(
            from_email=complete_from,
            to_emails=recipients,
            subject=subject,
            html_content=body if is_html else None,
            plain_text_content=None if is_html else body
        )

        # Handle attachments if needed
        if attachments:
            for att in attachments:
                content = att.get("content", "")
                filename = att.get("filename", "attachment")
                file_type = att.get("type", "application/octet-stream")
                disposition = att.get("disposition", "attachment")
                content_id = att.get("content_id", "")

                attach_obj = Attachment(
                    FileContent(content),
                    FileName(filename),
                    FileType(file_type),
                    Disposition(disposition),
                    ContentId(content_id)
                )
                message.add_attachment(attach_obj)

        try:
            response = self.client.send(message)
            logger.info("Email request sent to SendGrid")
            return {
                "status_code": response.status_code,
                "body": response.body.decode("utf-8") if response.body else None,
                "headers": dict(response.headers),
                "success": 200 <= response.status_code < 300
            }
        except Exception as e:
            logger.error(f"SendGrid API error: {e}", exc_info=True)
            raise

    def render_template(self, template_name: str, context_data: Dict[str, Any]) -> str:
        """
        Render a Jinja2 template with the given context.
        """
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context_data)
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}", exc_info=True)
            raise

    def list_templates(self) -> List[str]:
        """
        List template files in the configured template directory.
        """
        if not os.path.isdir(self.template_dir):
            logger.warning(f"Template directory {self.template_dir} does not exist")
            return []
        try:
            files = os.listdir(self.template_dir)
            # e.g., accept .html, .j2, .txt
            return [f for f in files if f.endswith((".html", ".j2", ".txt"))]
        except Exception as e:
            logger.error(f"Error listing templates in {self.template_dir}: {e}", exc_info=True)
            return []
