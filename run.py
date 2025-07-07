from web.backend.server import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)