import psycopg2
from fastapi import HTTPException

# Connect to the database
def connect():
    return psycopg2.connect("dbname=dbnantoka user=nantoka password=nantoka host=127.0.0.1 port=5066")

# Check if the book exists in the database
def existing_book(isbn):
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM book_details WHERE isbn = %s;', (isbn,))
            res = cur.fetchone()
            if res[0] > 0:
                raise HTTPException(status_code=400, detail="ISBN already exists")
