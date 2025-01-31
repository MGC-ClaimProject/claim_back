# claim_back
백엔드 레포입니다

brew install poetry
pip install poetry

brew install postgresql
pip install postgresql

brew services start postgresql

psql postgres
create database claim;
\q , \du
CREATE USER postgres WITH SUPERUSER CREATEDB CREATEROLE PASSWORD 'postgres';




poetry init
poetry shell
poetry install

python manage.py migrate
