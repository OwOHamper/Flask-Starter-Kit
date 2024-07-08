FROM python:3.9

WORKDIR /app

RUN wget https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64 -O tailwindcss && \
    chmod +x tailwindcss

# RUN apt-get update && apt-get install -y nodejs npm

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .

# RUN npm install
# RUN npx tailwindcss -i ./static/src/input.css -o ./static/dist/css/output.css --minify
RUN ./tailwindcss -i ./static/src/input.css -o ./static/dist/css/output.css --minify

RUN pybabel compile -d translations

RUN rm tailwindcss

CMD ["python", "server.py"]