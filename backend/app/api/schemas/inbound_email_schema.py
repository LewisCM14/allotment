"""
Inbound Email Schema
- Resend inbound webhook payload structure
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class InboundEmailAttachment(BaseModel):
    """Attachment metadata from inbound email."""

    content: str  # Base64 encoded
    content_type: str
    filename: str
    size: int


class InboundEmailData(BaseModel):
    """Inner data object for Resend inbound events."""

    # Enable alias population for fields like `from`
    model_config = ConfigDict(populate_by_name=True)

    from_: EmailStr = Field(alias="from")
    to: list[EmailStr]
    subject: Optional[str] = None
    text: Optional[str] = None
    html: Optional[str] = None
    cc: list[EmailStr] = Field(default_factory=list)
    bcc: list[EmailStr] = Field(default_factory=list)
    attachments: list[InboundEmailAttachment] = Field(default_factory=list)
    message_id: Optional[str] = None
    email_id: Optional[str] = None
    reply_to: Optional[str] = None
    created_at: Optional[datetime] = None


class InboundEmailPayload(BaseModel):
    """
    Resend inbound webhook payload envelope.
    """

    # Also allow name/alias population at the envelope level (future-proofing)
    model_config = ConfigDict(populate_by_name=True)

    type: str  # e.g. "email.received"
    created_at: Optional[datetime] = None
    data: InboundEmailData
