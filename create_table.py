import psycopg2

with psycopg2.connect("dbname=dbnantoka user=nantoka password=nantoka host=127.0.0.1 port=5066") as conn:
    with conn.cursor() as cur:

        cur.execute('''
            CREATE TABLE IF NOT EXISTS book_details (
                id SERIAL PRIMARY KEY,
                isbn TEXT NOT NULL,
                title TEXT,
                authors TEXT,
                copy_type TEXT,
                publisher TEXT,
                publishedDate TEXT,
                description TEXT
            )
        ''')
        conn.commit()