from fastapi import APIRouter, HTTPException, status
from app.models.request import ExecuteRequest
from app.models.response import ExecuteResponse
from app.services.executor import CodeExecutor

# Create router
router = APIRouter()

# Create executor instance
executor = CodeExecutor()


@router.post("/execute", response_model=ExecuteResponse)
async def execute_code(request: ExecuteRequest) -> ExecuteResponse:
    """
    Execute Python code.
    
    Args:
        request: ExecuteRequest with code to execute
        
    Returns:
        ExecuteResponse with stdout, stderr, or error
    """
    try:
        # Execute the code
        stdout, stderr, error = executor.execute(request.code)
        
        # If there's a system error, return HTTP 500
        if error and error == "Internal server error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
        
        # Return response (with stdout/stderr or error)
        return ExecuteResponse(
            stdout=stdout,
            stderr=stderr,
            error=error
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        # Catch any unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )