FROM python:3.9
RUN pip install ipython-sql sqlalchemy psycopg2-binary jupyter pgspecial pandas geopandas matplotlib geopandas dask plotly girder_client

RUN pip install girder_client pymongo



RUN python -m pip install "dask[distributed]" --upgrade 

RUN pip install colormath pgvector sqlmodel psycopg2 geoalchemy2
EXPOSE 8888
RUN mkdir /app
WORKDIR /app

COPY jupyter_notebook_config.json /root/.jupyter/jupyter_notebook_config.json

#RUN pip install large-image[all] --find-links https://girder.github.io/large_image_wheels



ENTRYPOINT [ "jupyter","notebook","--allow-root","--ip","0.0.0.0", "--NotebookApp.token=''", "--NotebookApp.password=''" ]
