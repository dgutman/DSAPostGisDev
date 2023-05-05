
docker stop dsapostgisapi
docker rm dsapostgisapi
docker run -it -v ${PWD}/app:/code/app --name dsapostgisapi dsapostgisapi /bin/bash
