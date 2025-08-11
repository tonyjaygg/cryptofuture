FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install -e .
CMD ["python", "cli/bot.py", "live", "BTCUSDT"]
