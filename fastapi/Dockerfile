
FROM python:3.9

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install colormath pgvector
## TO DO, figure out the version and just put it in the requirements

COPY ./app /code/app

EXPOSE 82

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "82","--reload"]
