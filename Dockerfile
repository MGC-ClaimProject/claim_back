# Python 3.13 최신 버전 사용
FROM python:3.13

# 작업 디렉토리 설정
WORKDIR /app/src

# 필수 패키지 설치
RUN pip install --no-cache-dir poetry

# Poetry 환경 설정
RUN poetry config virtualenvs.create false

# 프로젝트 의존성 설치 및 gunicorn 추가
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

# 프로젝트 코드 복사
COPY . .

# 서버 실행 명령어
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
