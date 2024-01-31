#!/bin/sh

exec uvicorn app.main:create_app --factory --proxy-headers --host $HOST --port $PORT
