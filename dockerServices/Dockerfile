FROM python:3.9-slim-buster

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update \
  # dependencies for building Python packages
  && apt-get install -y build-essential \
  # psycopg2 dependencies
  && apt-get install -y libpq-dev \
  # Additional dependencies
  && apt-get install -y telnet netcat \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# Requirements are installed here to ensure they will be cached.
COPY ./dockerServices/requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

# COPY ./compose/local/flask/entrypoint /entrypoint
# RUN sed -i 's/\r$//g' /entrypoint
# RUN chmod +x /entrypoint

COPY ./dockerServices/flask/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

COPY ./dockerServices/celery/worker/start /start-celeryworker
RUN sed -i 's/\r$//g' /start-celeryworker
RUN chmod +x /start-celeryworker

COPY ./dockerServices/celery/beat/start /start-celerybeat
RUN sed -i 's/\r$//g' /start-celerybeat
RUN chmod +x /start-celerybeat

COPY ./dockerServices/celery/flower/start /start-flower
RUN sed -i 's/\r$//g' /start-flower
RUN chmod +x /start-flower

WORKDIR /app

# ENTRYPOINT ["/entrypoint"]
