# syntax=docker/dockerfile:1
FROM python:3.9
ENV PYTHONUNBUFFERED=1
ENV TIMEOUT=120
WORKDIR /code
RUN python -m pip install --upgrade pip --no-cache-dir
COPY requirements.txt /code/
RUN python -m pip install -r requirements.txt --no-cache-dir
COPY . /code/
