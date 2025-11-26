import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",  # Notice: app.main (folder.file)
        host="0.0.0.0",
        port=8000,
        reload=True
    )