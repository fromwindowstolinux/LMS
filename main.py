from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from routes.auth import auth_router
from routes.book import book_router

app = FastAPI()

# Include routes from separate modules
app.include_router(auth_router)
app.include_router(book_router)

templates = Jinja2Templates(directory="templates")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
