FROM python:3.13

RUN pip install --upgrade pip wheel "poetry"

COPY shared ./shared

WORKDIR /app

COPY task-api/pyproject.toml task-api/poetry.lock ./

RUN poetry config virtualenvs.create false

RUN poetry install --no-root


COPY task-api/ .


CMD ["python", "-m", "src.main"]