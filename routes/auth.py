from fastapi import APIRouter, Request, Form, Depends, Cookie, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_302_FOUND
from fastapi.templating import Jinja2Templates
from auth import get_current_user
from database import connect

auth_router = APIRouter()
templates = Jinja2Templates(directory="templates")

SECRET_USERNAME = "testuser"
SECRET_PASSWORD = "password123"

# Login page (GET)
@auth_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Handle login form submission (POST)
@auth_router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    # Debugging print statements
    print(f"Attempting login with username: {username} and password: {password}")

    if username == SECRET_USERNAME and password == SECRET_PASSWORD:
        response = RedirectResponse(url="/layout", status_code=HTTP_302_FOUND)
        # Set the session cookie
        response.set_cookie(key="session_id", value="logged_in")  
        print(f"Login successful. Redirecting to /layout")
        return response
    else:
        print(f"Login failed. Invalid credentials for username: {username}")
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

# Logout route
@auth_router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=HTTP_302_FOUND)
    # Clear the session cookie
    response.delete_cookie(key="session_id")  
    return response

# Secure route : Layout page
@auth_router.get("/layout", response_class=HTMLResponse)
async def render_layout_page(request: Request, is_authenticated: bool = Depends(get_current_user)):
    if not is_authenticated:
        print(f"User is not authenticated. Redirecting to /login")
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)  # Redirect to login if not logged in
    print(f"User is authenticated. Rendering layout page.")
    return templates.TemplateResponse("isbn_form.html", {"request": request})

# Get list of book details
# @auth_router.get("/book-details", response_class=HTMLResponse)
# async def get_book_details(request: Request, sort_on: str = "authors", is_authenticated: bool = Depends(get_current_user)):
#     if not is_authenticated:
#         return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)
    
#     book_details_list = []
#     try:
#         with connect() as conn:
#             with conn.cursor() as cur:
#                 cur.execute('SELECT isbn, title, authors, copy_type, publisher, publishedDate, description FROM book_details;')
#                 book_details_list = cur.fetchall()

#         sort_index = {
#             "isbn": 0,
#             "title": 1,
#             "authors": 2,
#             "copy_type": 3,
#             "publisher": 4,
#             "publishedDate": 5,
#         }.get(sort_on, 0)

#         book_details_list.sort(key=lambda x: x[sort_index])

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

#     return templates.TemplateResponse("book-details.html", {"request": request, "book_details_list": book_details_list})