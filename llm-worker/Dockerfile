FROM python:3.13

RUN pip install --upgrade pip wheel "poetry"

COPY shared ./shared

WORKDIR /app

COPY llm-worker/pyproject.toml llm-worker/poetry.lock ./

RUN poetry config virtualenvs.create false

RUN poetry install --no-root


COPY llm-worker/ .


CMD ["python", "-m", "src.main"]