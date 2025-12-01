from pydantic import BaseModel, Field
from typing import Optional


class ExecuteRequest(BaseModel):
    """Request model for code execution."""
    id: Optional[str] = Field(
        None,
        description="Optional session ID to continue existing interpreter session"
    )
    code: str = Field(
        ..., 
        min_length=1,
        max_length=10000,
        description="Python code to execute"
    )