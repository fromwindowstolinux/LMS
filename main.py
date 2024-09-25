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
                    authors = book.get("authors", [])
                    authors_cleaned = ", ".join(authors)
                    published_date = book.get("publishedDate", "")
                    published_year = published_date[:4] if published_date else ""
                    # clean authors here
                    return {
                        "title": book.get("title", ""),
                        "authors": authors_cleaned,
                        "publisher": book.get("publisher", ""),
                        "publishedDate": published_year,
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
async def get_book_details(request: Request, sort_on: str = "authors"):
    book_details_list = []
    try:
        with psycopg2.connect("dbname=dbnantoka user=nantoka password=nantoka host=127.0.0.1 port=5066") as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT isbn, title, authors, copy_type, publisher, publishedDate, description FROM book_details;')
                book_details_list = cur.fetchall()

    # Sorting logic
        sort_index = {
            "isbn": 0,
            "title": 1,
            "authors": 2,
            "copy_type": 3,
            "publisher": 4,
            "publishedDate": 5,
        }.get(sort_on, 0)

        # Sort the list by the specified column index
        book_details_list.sort(key=lambda x: x[sort_index])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return templates.TemplateResponse("book-details.html", {"request": request, "book_details_list": book_details_list})


# Retrieve a specific book's details by ISBN
@app.get("/book-info/{isbn}", response_class=HTMLResponse)
async def render_book_info(request: Request, isbn: str):
    print(f"Fetching book info for ISBN: {isbn}")  # Debugging statement
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''SELECT isbn, title, authors, publisher, publishedDate, description 
                       FROM book_details WHERE isbn = %s;''', (isbn,)
                )
                book_details = cur.fetchone()
                print(f"Book details fetched: {book_details}")  # Debugging statement

                if not book_details:
                    print("Book not found in database")  # Debugging statement
                    raise HTTPException(status_code=404, detail="Book not found")

                return templates.TemplateResponse("book-info.html", {
                    "request": request,
                    "isbn": book_details[0],
                    "title": book_details[1],
                    "authors": book_details[2],
                    "publisher": book_details[3],
                    "publishedDate": book_details[4],
                    "description": book_details[5]
                })
    except Exception as e:
        print(f"Error occurred: {e}")  # Debugging statement
        raise HTTPException(status_code=500, detail=str(e))


# Edit a book's details (GET request to render the edit form)
@app.get("/edit-book/{isbn}", response_class=HTMLResponse)
async def render_edit_book_form(request: Request, isbn: str):
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''SELECT isbn, title, authors, publisher, publishedDate, description, copy_type 
                       FROM book_details WHERE isbn = %s;''', (isbn,)
                )
                book_details = cur.fetchone()

                if not book_details:
                    raise HTTPException(status_code=404, detail="Book not found")

                return templates.TemplateResponse("edit-book.html", {
                    "request": request,
                    "isbn": book_details[0],
                    "title": book_details[1],
                    "authors": book_details[2],
                    "publisher": book_details[3],
                    "published_date": book_details[4],
                    "description": book_details[5],
                    "copy_type": book_details[6]
                })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Edit a book's details (POST request to submit the updated form)
@app.get("/book-info/{isbn}", response_class=HTMLResponse)
async def render_book_info(request: Request, isbn: str):
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''SELECT isbn, title, authors, type, publisher, publishedDate, description, image_url 
                       FROM book_details WHERE isbn = %s;''', (isbn,)
                )
                book_details = cur.fetchone()

                if not book_details:
                    raise HTTPException(status_code=404, detail="Book not found")

                return templates.TemplateResponse("book-info.html", {
                    "request": request,
                    "isbn": book_details[0],
                    "title": book_details[1],
                    "authors": book_details[2],
                    "publisher": book_details[4],
                    "published_date": book_details[5],
                    "description": book_details[6],
                    "url": book_details[7]  # Pass the image URL to the template
                })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/update-book/{isbn}")
async def update_book(isbn: str, request: Request):
    form_data = await request.form()

    title = form_data['title']
    authors = form_data['authors']
    publisher = form_data['publisher']
    published_year = form_data['published_year']
    copy_type = form_data['copy_type']
    description = form_data['description']

    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute('''UPDATE book_details 
                               SET  title = %s, 
                                    authors = %s, 
                                    publisher = %s, 
                                    publishedDate = %s, 
                                    copy_type = %s, 
                                    description = %s 
                               WHERE isbn = %s;''',
                            (title, authors, publisher, published_year, copy_type, description, isbn))

                conn.commit()

        # Redirect to updated book info page
        return RedirectResponse(url=f"/book-info/{isbn}", status_code=303)
    except Exception as e:
        print(f"Error occurred while updating book: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

