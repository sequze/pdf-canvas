FROM python:3.13

RUN pip install --upgrade pip wheel "poetry"

COPY shared ./shared

WORKDIR /app

COPY api-gateway/pyproject.toml api-gateway/poetry.lock ./

RUN poetry config virtualenvs.create false

RUN poetry install --no-root


COPY api-gateway/ .


CMD ["python", "-m", "src.main"]