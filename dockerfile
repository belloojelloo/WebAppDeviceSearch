FROM python:3.11-slim

WORKDIR /app

# System dependencies for Playwright browsers
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    ffmpeg \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxfixes3 \
    libxi6 \
    libxtst6 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libpango-1.0-0 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium
RUN playwright install --with-deps chromium

COPY . .

# Run Flask app (app.py with Flask "app" instance)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:${PORT}"]
