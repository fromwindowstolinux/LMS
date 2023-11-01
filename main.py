from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import psycopg2
import httpx
import traceback
import typing
from typing import Annotated

app = FastAPI()
templates = Jinja2Templates(directory="templates")
users = {'testuser@test': 'testuser'}

# login page
@app.get("/login", response_class=HTMLResponse)
async def render_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def check_login(request: Request, email: Annotated[str, Form()], password: Annotated[str, Form()]): 
    print(email, password) 
    if email in users and users[email] == password: 
        return RedirectResponse("/layout", status_code=302)
    else:  
        return templates.TemplateResponse("login.html", {"request": request, "message": "Invalid username or password. Please try again."})

# layout page
@app.get("/layout", response_class=HTMLResponse)
async def render_layout_page(request: Request):
    return templates.TemplateResponse("layout.html", {"request": request})

# https://fastapi.tiangolo.com/tutorial/security/first-steps/

# sign up page
@app.get("/signup", response_class=HTMLResponse)
async def render_sign_up_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

# connect to database
def connect():
    return psycopg2.connect("dbname=dbnantoka user=nantoka password=nantoka host=127.0.0.1 port=5066")

# check if the book exists in the database
def existing_book(isbn):
    print('existing book')
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute('''SELECT COUNT(*) FROM book_details WHERE isbn = %s;''', (isbn,))
            res = cur.fetchone()
            if res[0] > 0:
                raise HTTPException(status_code=400, detail="ISBN already exists")

# isbn form
@app.get("/isbn")
async def render_isbn_form(request: Request):
    return templates.TemplateResponse("isbn_form.html", {"request": request})

# process submitted isbn
@app.get("/submit-isbn/")
async def process_isbn(isbn: str):
    if existing_book(isbn):
        raise HTTPException(status_code=400, detail="Book already exists in the database")

    return {"message": "ISBN received successfully", "isbn": isbn}

# fetch book details from Google Books API
async def new_books(isbn):
    key = "AIzaSyBM_Ft994Rb5a3zTnYFHSNBTtbpwRmW9pE"
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&key={key}"
    print ('new book')
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                if "items" in data:
                    book = data["items"][0]["volumeInfo"]
                    return {
                        "title": book.get("title", ""),
                        "authors": book.get("authors", []),
                        "publisher": book.get("publisher", ""),
                        "publishedDate": book.get("publishedDate", ""),
                        "description": book.get("description", "")
                    }
                else:
                    raise HTTPException(status_code=404, detail="Book not found")
            else:
                raise HTTPException(status_code=500, detail="Failed to fetch book details")

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to retrieve book details")

# retrieve book details
@app.post("/isbn")
async def retrieve_book_details(isbn: typing.Annotated[str, Form()], 
                                copy_type: typing.Annotated[str, Form()]):
    if not existing_book(isbn):
        book_details = await new_books(isbn)
        print(book_details)
        try:
            # Insert book details into the database
            with connect() as conn:
                with conn.cursor() as cur:
                    cur.execute('''
                            INSERT INTO book_details (isbn, title, authors, copy_type, publisher, publishedDate, description)
                            VALUES (%s, %s, %s, %s, %s, %s, %s);
                        ''', (isbn,
                              book_details["title"],
                              book_details["authors"],
                              copy_type,
                              book_details["publisher"],
                              book_details["publishedDate"],
                              book_details["description"]
                              ))
                    conn.commit()
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail="Failed to insert book details into the database")
        return {"message": "Book details inserted successfully"}
    
    else:
        raise HTTPException(status_code=400, detail="Book already exists in the database")

@app.get("/book-details")
async def get_book_details(request: Request):
    book_details_list = []
    try:
        with psycopg2.connect("dbname=dbnantoka user=nantoka password=nantoka host=127.0.0.1 port=5066") as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT isbn, title, authors, copy_type, publisher, publishedDate, description FROM book_details;')
                book_details_list = cur.fetchall()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return templates.TemplateResponse("book-details.html", {"request": request, "book_details_list": book_details_list})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

