from pydantic import BaseModel, Field


class ExecuteRequest(BaseModel):
    """Request model for code execution."""
    code: str = Field(
        ..., 
        min_length=1,
        max_length=10000,
        description="Python code to execute"
    )