FROM python:3.11-slim
LABEL maintainer="x-entropy at pm.me"

WORKDIR /usr/src/app

RUN apt-get update \
    && apt-get install -y ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


COPY app /usr/src/app/app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENV PORT 8000
ENV HOST 0.0.0.0
ENV NAME hls_streamer
ENV ENABLE_DISCOVERY "False"

EXPOSE $PORT

CMD uvicorn --factory app.main:create_app --host $HOST --port $PORT
