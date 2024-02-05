FROM python:3.11-slim
LABEL maintainer="x-entropy at pm.me"

WORKDIR /usr/src/app

RUN apt-get update \
    && apt-get install -y \
    tini \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

COPY app /usr/src/app/app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENV PORT 8081
ENV PROM_PORT 8000
ENV HOST 0.0.0.0
ENV NAME hls_streamer
ENV ENABLE_DISCOVERY "False"

EXPOSE $PORT

ENTRYPOINT ["tini", "--", "./entrypoint.sh"]
