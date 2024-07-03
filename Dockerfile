FROM python:3.9

WORKDIR /app

RUN apt-get update && apt-get install -y nodejs npm

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .

RUN npm install
RUN npm tailwindcss -i ./static/css/input.css -o ./static/dist/css/output.css --minify

RUN pybabel compile -d translations

CMD ["python", "server.py"]