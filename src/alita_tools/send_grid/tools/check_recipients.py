import logging
import traceback
from typing import List, Type
from langchain_core.tools import BaseTool, ToolException
from pydantic import BaseModel, Field, create_model

logger = logging.getLogger(__name__)

class CheckRecipientsTool(BaseTool):
    """
    Tool that checks recipients list for suspicious domains or large distribution.
    Returns a user-friendly message if suspicious or asks for confirmation.
    """
    name: str = "check_recipients"
    description: str = (
        "Check a list of recipients for suspicious domains or large distribution. "
        "Warn user or ask for confirmation if needed."
    )

    args_schema: Type[BaseModel] = create_model(
        "CheckRecipientsArgs",
        recipients=(List[str], Field(..., description="List of email addresses to check")),
        large_dist_threshold=(int, Field(default=5, description="If recipients exceed this number, ask for confirmation")),
        suspicious_domains=(List[str], Field(default=["example.com", "test.com"], description="List of domains to flag"))
    )

    def _run(self, recipients: List[str], large_dist_threshold: int = 5, suspicious_domains: List[str] = None) -> str:
        suspicious_domains = suspicious_domains or ["example.com", "test.com"]
        logger.info(f"Checking {len(recipients)} recipients for suspicious patterns...")

        if not recipients:
            return "⚠️ No recipients provided. Please add at least one email address."

        # Check for large distribution
        if len(recipients) > large_dist_threshold:
            return (
                f"🚨 You have {len(recipients)} recipients, which is above the threshold of {large_dist_threshold}. "
                "Are you sure you want to send to so many people?"
            )

        # Check suspicious domains
        flagged = []
        for r in recipients:
            domain = r.split("@")[-1].lower()
            if domain in suspicious_domains:
                flagged.append(r)

        if flagged:
            return (
                "⚠️ The following recipients are from suspicious or test domains:\n"
                + "\n".join(flagged)
                + "\nDo you want to proceed?"
            )

        return "✅ Recipients look good. OK to send."

__all__ = [
    {"name": "check_recipients", "tool": CheckRecipientsTool}
]