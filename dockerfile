FROM python:3.11-slim
WORKDIR /app

# ПРИНУДИТЕЛЬНО ставим правильную версию aiogram
RUN pip install --no-cache-dir --upgrade aiogram==3.7.0 aiohttp

# Копируем остальные файлы
COPY . .

# Запускаем бота
CMD ["python", "bot.py"]