FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pybabel compile -d translations

COPY . .

CMD ["python", "server.py"]