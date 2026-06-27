FROM python:3.12-slim

WORKDIR /app

# Playwright / patchright 依赖 (scrapling headless) — 直接安装 .deb，避开 GPG key 问题
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget \
    fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-freefont-ttf \
    libglib2.0-0t64 libnspr4 libnss3 libatk1.0-0t64 libatk-bridge2.0-0t64 \
    libdbus-1-3 libcups2t64 libxcb1 libxkbcommon0 libasound2t64 libgbm1 \
    libx11-6 libxext6 libcairo2 libpango-1.0-0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libatspi2.0-0t64 \
    && wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome-stable_current_amd64.deb 2>/dev/null; apt-get install -f -y --no-install-recommends \
    && rm -f google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python3 -m playwright install chromium 2>/dev/null || true

COPY *.py ./

EXPOSE 8000

CMD ["python3", "main.py"]
