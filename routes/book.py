from fastapi import APIRouter, Request, Form, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from auth import get_current_user
from database import connect, existing_book
import httpx
import traceback
from typing import Annotated
from starlette.status import HTTP_302_FOUND

book_router = APIRouter()
templates = Jinja2Templates(directory="templates")

# ISBN form page (only accessible after login)
@book_router.get("/isbn", response_class=HTMLResponse)
async def render_isbn_form(request: Request, is_authenticated: bool = Depends(get_current_user)):
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)
    return templates.TemplateResponse("isbn_form.html", {"request": request})

# Process submitted ISBN (only accessible after login)
@book_router.get("/submit-isbn/", response_class=HTMLResponse)
async def process_isbn(isbn: str, is_authenticated: bool = Depends(get_current_user)):
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)

    if existing_book(isbn):
        raise HTTPException(status_code=400, detail="Book already exists in the database")

    return {"message": "ISBN received successfully", "isbn": isbn}

# Fetch book details from Google Books API
async def new_books(isbn):
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                if "items" in data:
                    book = data["items"][0]["volumeInfo"]
                    authors_cleaned = ", ".join(book.get("authors", []))
                    published_year = book.get("publishedDate", "")[:4]
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

# Retrieve book details
@book_router.post("/isbn")
async def retrieve_book_details(isbn: Annotated[str, Form()], copy_type: Annotated[str, Form()]):
    if not existing_book(isbn):
        book_details = await new_books(isbn)
        try:
            with connect() as conn:
                with conn.cursor() as cur:
                    cur.execute('''
                            INSERT INTO book_details (isbn, title, authors, copy_type, publisher, publishedDate, description)
                            VALUES (%s, %s, %s, %s, %s, %s, %s);
                        ''', (isbn, book_details["title"], book_details["authors"], copy_type, book_details["publisher"],
                              book_details["publishedDate"], book_details["description"]))
                    conn.commit()
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail="Failed to insert book details into the database")
        return {"message": "Book details inserted successfully"}
    else:
        raise HTTPException(status_code=400, detail="Book already exists in the database")

# Edit a book's details (GET request to render the edit form)
@book_router.get("/edit-book/{isbn}", response_class=HTMLResponse)
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
@book_router.get("/book-info/{isbn}", response_class=HTMLResponse)
async def render_book_info(request: Request, isbn: str):
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''SELECT isbn, title, authors, publisher, publishedDate, description, url 
                       FROM book_details WHERE isbn = %s;''', (isbn,)
                )
                book_details = cur.fetchone()

                if not book_details:
                    raise HTTPException(status_code=404, detail="Book not found")
                print(book_details[6])
                return templates.TemplateResponse("book-info.html", {
                    "request": request,
                    "isbn": book_details[0],
                    "title": book_details[1],
                    "authors": book_details[2],
                    "publisher": book_details[3],
                    "published_date": book_details[4],
                    "description": book_details[5],
                    "url": book_details[6]  # Pass the image URL to the template
                })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update book
@book_router.post("/update-book/{isbn}")
async def update_book(isbn: str, request: Request):
    form_data = await request.form()

    title = form_data['title']
    authors = form_data['authors']
    publisher = form_data['publisher']
    published_year = form_data['published_year']
    copy_type = form_data['copy_type']
    description = form_data['description']
    url = form_data['url']

    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute('''UPDATE book_details 
                               SET  title = %s, 
                                    authors = %s, 
                                    publisher = %s, 
                                    publishedDate = %s, 
                                    copy_type = %s, 
                                    description = %s, 
                                    url = %s
                               WHERE isbn = %s;''',
                            (title, authors, publisher, published_year, copy_type, description, url, isbn))

                conn.commit()

        # Redirect to updated book info page
        return RedirectResponse(url=f"/book-info/{isbn}", status_code=303)
    except Exception as e:
        print(f"Error occurred while updating book: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
# Delete a book based on ISBN
@book_router.post("/delete-book/{isbn}")
async def delete_book(isbn: str, is_authenticated: bool = Depends(get_current_user)):
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)

    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT COUNT(*) FROM book_details WHERE isbn = %s', (isbn,))
                if cur.fetchone()[0] == 0:
                    raise HTTPException(status_code=404, detail="Book not found")

                cur.execute('DELETE FROM book_details WHERE isbn = %s', (isbn,))
                conn.commit()

        return RedirectResponse(url="/book-details", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Get total count of books for pagination
def get_total_books():
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM book_details;')
            total_books = cur.fetchone()[0]
    return total_books

# Helper function to format author names as "Family Name, Given Name"
def format_author_name(author_name):
    """
    Formats the author name to "Family Name, Given Names" format.
    Returns both formatted name and family name for sorting.
    """
    name_parts = author_name.split()
    if len(name_parts) > 1:
        family_name = name_parts[-1]
        given_names = " ".join(name_parts[:-1])
        formatted_name = f"{family_name}, {given_names}"
        return formatted_name, family_name  # Return formatted name and family name
    else:
        return author_name, author_name  # For single name authors, return it as is for both

# Get list of book details with formatted author names
@book_router.get("/book-details", response_class=HTMLResponse)
async def get_book_details(request: Request, 
                           sort_on: str = "authors", 
                           limit: int = Query(10, ge=1), 
                           offset: int = Query(0, ge=0), 
                           search: str = Query("", description="Search term to filter books"), 
                           is_authenticated: bool = Depends(get_current_user)):
    if not is_authenticated:
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)

    book_details_list = []
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                # Adjust query to include search functionality and fetch all book details
                query = '''SELECT isbn, title, authors, copy_type, publisher, publishedDate, description
                           FROM book_details
                           WHERE LOWER(title) LIKE %s OR LOWER(authors) LIKE %s;'''
                search_term = f"%{search.lower()}%"
                cur.execute(query, (search_term, search_term))
                book_details_list = cur.fetchall()

        # Format authors and extract family name for sorting
        formatted_books = [
            (
                book[0],  # ISBN
                book[1],  # Title
                ", ".join([format_author_name(author)[0] for author in book[2].split(", ")]),  # Formatted authors
                book[3],  # Copy Type
                book[4],  # Publisher
                book[5],  # Published Year
                book[6],  # Description
                format_author_name(book[2].split(", ")[0])[1]  # First author's family name for sorting
            ) for book in book_details_list
        ]

        # Sort all books by the first author's family name in ascending order
        formatted_books.sort(key=lambda x: x[7])  # Sort by the family name

        # Apply pagination after sorting
        total_books = len(formatted_books)  # Total number of books after sorting and filtering
        paginated_books = formatted_books[offset:offset + limit]  # Slice the sorted list for pagination
        total_pages = (total_books + limit - 1) // limit
        current_page = (offset // limit) + 1

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return templates.TemplateResponse("book-details.html", {
        "request": request,
        "book_details_list": paginated_books,  # Pass only the paginated slice
        "total_pages": total_pages,
        "current_page": current_page,
        "limit": limit,
        "search": search  # Pass search term back to the template
    })

