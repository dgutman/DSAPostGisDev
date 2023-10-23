FROM python:3.6

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv/celery

COPY ./app app
COPY ./requirements.txt /tmp/requirements.txt
COPY ./celery.sh celery.sh

RUN pip install --no-cache-dir \
    -r /tmp/requirements.txt

VOLUME ["/var/log/celery", "/var/run/celery"]

CMD ["./celery.sh"]


https://stackoverflow.com/questions/59651428/runtimewarningyoure-running-the-worker-with-superuser-privilegesthis-is-absol


where celery.sh looks as follows:

#!/usr/bin/env bash

mkdir -p /var/run/celery /var/log/celery
chown -R nobody:nogroup /var/run/celery /var/log/celery

exec celery --app=app worker \
            --loglevel=INFO --logfile=/var/log/celery/worker-example.log \
            --statedb=/var/run/celery/worker-example@%h.state \
            --hostname=worker-example@%h \
            --queues=celery.example -O fair \
            --uid=nobody --gid=nogroup