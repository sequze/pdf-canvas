FROM python:3.13


RUN pip install --upgrade pip wheel "poetry"

COPY shared ./shared

WORKDIR /app

COPY pdf-worker/pyproject.toml pdf-worker/poetry.lock ./

RUN poetry config virtualenvs.create false

RUN poetry install --no-root

# Установка системных зависимостей для Playwright
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN playwright install chromium

COPY pdf-worker/ .

CMD ["python", "-m", "src.main"]