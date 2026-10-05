"""
Global field-level error handling.

A single, consistent exception type for any error that can be tied to one
specific request field (e.g. "ABN already exists" -> field="abn"). Raise
this instead of a plain HTTPException whenever the error is about a
particular field's value, so the frontend can render the message directly
beside that field instead of in a generic banner/toast.

Usage (replaces `raise HTTPException(status_code=409, detail="...")`):

    from app.core.exceptions import FieldValidationError

    if existing_abn:
        raise FieldValidationError(
            field="abn",
            message=f"An organization with ABN {abn} is already registered",
            status_code=409,
        )

The registered exception handler (see app/main.py) converts this into a
JSON response shaped as:

    {
        "detail": "<message>",             # unchanged shape — existing frontend
                                            #   code reading `detail` as a plain
                                            #   string keeps working untouched.
        "field_errors": {"abn": "<message>"}  # NEW — frontend reads this to
                                               #   render the error beside the
                                               #   matching field, when that
                                               #   field exists on the current
                                               #   screen.
    }

Pydantic/FastAPI validation errors (422s raised by @field_validator) are
reshaped into the exact same {"detail": ..., "field_errors": {...}} shape by
a second handler for RequestValidationError, so the frontend only ever needs
to understand one response format for both business-rule errors and
request-schema validation errors.
"""
from __future__ import annotations


class FieldValidationError(Exception):
    """Raise when a validation/business-rule error is tied to one specific field.

    field: the request field name (must match the field name the frontend
           form actually renders, e.g. "abn", "branch_code", "email").
    message: human-readable message, safe to show directly under the field.
    status_code: HTTP status to return (409 for "already exists" conflicts,
                 422 for format/business-rule validation failures).
    """

    def __init__(self, field: str, message: str, status_code: int = 409):
        self.field = field
        self.message = message
        self.status_code = status_code
        super().__init__(message)
