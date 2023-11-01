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

- Start docker, docker compose, and check status
```
sudo systemctl start docker
sudo docker compose up
docker ps 
```
- create and check table 
```
python3 create_table.py
psql -d [dbname] -U [username] -h [host] -p [port]
```
run the app
```
uvicorn main:app --reload
```

