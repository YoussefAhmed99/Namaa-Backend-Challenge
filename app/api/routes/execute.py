from fastapi import APIRouter, HTTPException, status
from app.models.request import ExecuteRequest
from app.models.response import ExecuteResponse
from app.services.session_manager import SessionManager

# Create router
router = APIRouter()

# Create session manager instance
session_manager = SessionManager()


@router.post("/execute", response_model=ExecuteResponse)
async def execute_code(request: ExecuteRequest) -> ExecuteResponse:
    try:
        # Execute the code (creates new session if id not provided)
        stdout, stderr, error, session_id = session_manager.execute(
            code=request.code,
            session_id=request.id
        )
        
        # If there's a system error, return HTTP 500
        if error and error == "Internal server error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
        
        # Return response (with session id and stdout/stderr or error)
        response = ExecuteResponse(
            id=session_id,
            stdout=stdout,
            stderr=stderr,
            error=error
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        # Catch any unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
        
        