from fastapi import FastAPI
from app.api.routes import execute

# Create FastAPI app
app = FastAPI(
    title="Python Code Executor",
    version="1.0.0",
    description="Execute Python code via HTTP API"
)

# Include the execute router
app.include_router(execute.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "Python Code Executor API"
    }