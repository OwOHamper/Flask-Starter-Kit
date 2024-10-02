FROM node:20 as css-builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY ./static/src ./static/src
COPY ./static/js ./static/js
COPY ./templates ./templates
COPY tailwind.config.js ./

RUN npx tailwindcss -i ./static/src/input.css -o ./static/dist/css/output.css --minify



FROM python:3.10.8-slim

ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install only the necessary dependencies for pybabel
RUN apt-get update && apt-get install -y --no-install-recommends \
    gettext \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .

COPY --from=css-builder /app/static/dist/css/output.css ./static/dist/css/

RUN pybabel compile -d translations

CMD ["python", "server.py"]