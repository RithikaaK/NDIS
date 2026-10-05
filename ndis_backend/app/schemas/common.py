"""Generic/utility schemas."""
from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Generic message response schema."""
    message: str
    success: bool = True
