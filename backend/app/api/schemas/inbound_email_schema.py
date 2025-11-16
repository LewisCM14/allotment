"""
Inbound Email Schema
- Resend inbound webhook payload structure
"""

from typing import Optional

from pydantic import BaseModel, EmailStr


class InboundEmailAttachment(BaseModel):
    """Attachment metadata from inbound email."""

    content: str  # Base64 encoded
    content_type: str
    filename: str
    size: int


class InboundEmailPayload(BaseModel):
    """
    Resend inbound webhook payload.
    """

    from_: EmailStr  # Sender email (aliased from 'from')
    to: str  # Recipient (e.g., contact@mail.allotment.wiki)
    subject: str
    text: Optional[str] = None  # Plain text body
    html: Optional[str] = None  # HTML body
    reply_to: Optional[str] = None
    attachments: Optional[list[InboundEmailAttachment]] = None

    class Config:
        populate_by_name = True
        fields = {"from_": {"alias": "from"}}
