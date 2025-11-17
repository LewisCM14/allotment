"""
Inbound Email Schema
- Resend inbound webhook payload structure
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class InboundEmailAttachment(BaseModel):
    """Attachment metadata from inbound email."""

    content: str  # Base64 encoded
    content_type: str
    filename: str
    size: int


class InboundEmailData(BaseModel):
    """Inner data object for Resend inbound events."""

    from_: EmailStr  # aliased from 'from'
    to: list[EmailStr]
    subject: Optional[str] = None
    text: Optional[str] = None
    html: Optional[str] = None
    cc: list[EmailStr] = []
    bcc: list[EmailStr] = []
    attachments: list[InboundEmailAttachment] = []
    message_id: Optional[str] = None
    email_id: Optional[str] = None
    reply_to: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        fields = {"from_": {"alias": "from"}}


class InboundEmailPayload(BaseModel):
    """
    Resend inbound webhook payload envelope.
    """

    type: str  # e.g. "email.received"
    created_at: Optional[datetime] = None
    data: InboundEmailData
