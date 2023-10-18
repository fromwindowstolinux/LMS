# Library Management System (LMS)

## Dependencies

Note: Do this in a Virtual Environment

1. Container

- Docker Engine: https://docs.docker.com/engine/install/fedora/

- Docker Compose: https://docs.docker.com/compose/install/linux/

2. Database

- Psycopg2 Library:
```
sudo dnf install python-devel postgresql-devel rpm-build

pip install psycopg2
```

4. Backend Framework: 
- FastAPI Library and ASGI server:
```
pip install "fastapi[all]"
pip install "uvicorn[standard]"
```
- async APIs
```
pip install httpx
``` 


## Run It!
```
docker compose up
python3 create_table.py
uvicorn main:app --reload
```
