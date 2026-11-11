import uvicorn

if __name__ == "__main__":
    print("Starting RAG Document Chat Backend on http://0.0.0.0:8000 ...")
    print("Interactive Swagger API Docs: http://localhost:8000/docs")
    uvicorn.run("backend.api.app:app", host="0.0.0.0", port=8000, reload=True)
