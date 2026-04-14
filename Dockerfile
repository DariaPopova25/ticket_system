FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./

RUN python -m pip install --upgrade pip \
    && pip install -r requirements-dev.txt

COPY . .

EXPOSE 8000
