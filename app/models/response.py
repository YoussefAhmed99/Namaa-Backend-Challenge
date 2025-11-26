from pydantic import BaseModel, model_validator
from typing import Optional

class ExecuteResponse(BaseModel):
    """Response model for code execution."""
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    error: Optional[str] = None
    
    @model_validator(mode='after')
    def check_mutual_exclusivity(self):
        """Ensure error and stdout/stderr are mutually exclusive."""
        has_error = self.error is not None
        has_output = self.stdout is not None or self.stderr is not None
        
        if has_error and has_output:
            raise ValueError(
                "Cannot have both 'error' and 'stdout/stderr' in response"
            )
        
        return self
    
    class Config:
        exclude_none = True  # Don't include None fields in JSON output