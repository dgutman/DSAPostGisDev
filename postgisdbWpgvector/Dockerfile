FROM postgis/postgis 
RUN apt-get update -y
RUN apt-get install  git postgresql-server-dev-15 make gcc -y
WORKDIR /tmp
RUN git clone --branch v0.4.2 https://github.com/pgvector/pgvector.git && cd pgvector && make && make install
