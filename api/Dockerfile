# syntax=docker/dockerfile:1
FROM python:3.8
ENV PYTHONUNBUFFERED=1
ENV TIMEOUT=120
WORKDIR /code
RUN python -m pip install --upgrade pip
COPY requirements.txt /code/
RUN python -m pip install -r requirements.txt
COPY . /code/
