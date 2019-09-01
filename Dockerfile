FROM python:3
ENV PYTHONBUFFERED 1

MAINTAINER curt.merrill@turner.com

RUN apt-get update -y

COPY . /app
WORKDIR /app

ENV PYTHONPATH /app

RUN pip install -r requirements.txt

CMD ["/app/start.sh"]
