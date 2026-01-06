# Project Analysis: Library Management System

This document provides a detailed analysis of the repository's stack and features to assist in redoing the project.

## 1. Tech Stack

### Backend
*   **Language:** Python 3
*   **Framework:** FastAPI (Web framework)
*   **Server:** Uvicorn (ASGI server)
*   **Template Engine:** Jinja2 (Server-side rendering)
*   **HTTP Client:** `httpx` (Async client for external API calls)

### Database
*   **Database:** PostgreSQL
*   **Driver:** `psycopg2-binary`
*   **ORM/Querying:** Raw SQL via `psycopg2` cursors

### DevOps / Infrastructure
*   **Containerization:** Docker
*   **Orchestration:** Docker Compose
*   **Database Service:** `postgres:latest` image
    *   **Internal Port:** 5432
    *   **External Port:** 5066
    *   **Credentials:** User: `nantoka`, Pass: `nantoka`, DB: `dbnantoka`

## 2. Features & Functionality

### Authentication
*   **Method:** Simple session-based authentication using a cookie (`session_id="logged_in"`).
*   **Credentials:** Hardcoded in `routes/auth.py` (`testuser` / `password123`).
*   **Endpoints:**
    *   `GET /login`: Renders login page.
    *   `POST /login`: Validates credentials and sets cookie.
    *   `GET /logout`: Clears cookie and redirects to login.
*   **Protection:** Routes check for the cookie via `get_current_user` dependency.

### Book Management
The core functionality revolves around managing a collection of books.

#### 1. Add Book (Import by ISBN)
*   **Endpoint:** `GET /submit-isbn/` (Check), `POST /isbn` (Save)
*   **Logic:**
    1.  User submits an ISBN.
    2.  System fetches metadata from **Google Books API** (`https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}`).
    3.  Extracts: Title, Authors, Publisher, Published Date, Description.
    4.  Inserts into local PostgreSQL database (`book_details` table).
    5.  Prevents duplicate ISBNs.

#### 2. List Books (Inventory)
*   **Endpoint:** `GET /book-details`
*   **Features:**
    *   **Search:** Filter by Title or Authors (case-insensitive substring match).
    *   **Sorting:** Sorts by **Author's Family Name** (Logic implemented in Python, not SQL).
    *   **Pagination:** Supports `limit` and `offset` (Logic applied in Python after fetching/sorting).
    *   **Display:** Shows formatted author names ("Family Name, Given Name").

#### 3. View Book Details
*   **Endpoint:** `GET /book-info/{isbn}`
*   **Features:** Displays detailed information including an image URL.

#### 4. Edit Book
*   **Endpoint:** `GET /edit-book/{isbn}`, `POST /update-book/{isbn}`
*   **Editable Fields:** Title, Authors, Publisher, Published Year, Copy Type, Description, URL.

#### 5. Delete Book
*   **Endpoint:** `POST /delete-book/{isbn}`
*   **Logic:** Removes the record from the database.

## 3. Database Schema

**Table:** `book_details`

| Column | Type | Notes |
| :--- | :--- | :--- |
| `id` | SERIAL PRIMARY KEY | Auto-incrementing ID |
| `isbn` | TEXT | Treated as unique identifier in logic |
| `title` | TEXT | |
| `authors` | TEXT | Comma-separated string |
| `copy_type` | TEXT | e.g., Hardcover, Paperback |
| `publisher` | TEXT | |
| `publishedDate` | TEXT | Stored as string (Year) |
| `description` | TEXT | |
| `url` | TEXT | **Note:** Missing in `create_table.py` but used in `routes/book.py`. This column must be added to the schema. |

## 4. External Dependencies
*   **Google Books API:** Used to fetch book metadata by ISBN.

## 5. Implementation Notes for Redesign
*   **Security:** Move away from hardcoded credentials and simple cookie checks. Use proper hashing (e.g., bcrypt) and JWT or secure session management.
*   **Database:**
    *   Standardize the schema (add `url` column properly).
    *   Use `isbn` as Primary Key or ensure unique constraint.
    *   Consider using an ORM (SQLAlchemy/SQLModel) instead of raw SQL strings.
*   **Performance:** Move sorting and pagination logic to the SQL query (`ORDER BY`, `LIMIT`, `OFFSET`) to handle large datasets efficiently.
*   **Data Integrity:** The `existing_book` check function has a logic flow issue (raises exception instead of returning boolean), which makes the conditional check in `routes/book.py` redundant/buggy.
