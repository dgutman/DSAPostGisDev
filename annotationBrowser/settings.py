## Do all login and DB stuff in here to make imports not a nightmare...
import girder_client, os
from dotenv import load_dotenv
import pymongo
import socket

load_dotenv()

DSAKEY = os.getenv("DSAKEY")
DSA_BASE_URL = "https://megabrain.neurology.emory.edu/api/v1"
# print(DSAKEY, "is dsa key")
gc = girder_client.GirderClient(apiUrl=DSA_BASE_URL)
if DSAKEY:
    gc.authenticate(apiKey=DSAKEY)


USER = "admin"

## MONGO CONNECTION INFORMATION

## Determine if I can connect to mongo and redis
## NOT USING REDIS ANYMORE... WILL MAYBE REINTEGRATE LATER
# try:
#     redis_host = socket.gethostbyname("redis")
#     # print(redis_host)
#     REDIS_URL = "redis://redis:6379"

# except:
#     print("Host lookup failed for REDIS")
#     REDIS_URL = "redis://localhost:6379"


MONGO_URI = "localhost:37017"
MONGODB_USERNAME = "docker"
MONGODB_PASSWORD = "docker"
MONGODB_HOST = "mongodb"
MONGODB_PORT = 27017
MONGODB_DB = "cacheDSAannotationData"
APP_IN_DOCKER = False


### Create mongo connection strings here as well
mongoConn = pymongo.MongoClient(
    MONGO_URI, username=MONGODB_USERNAME, password=MONGODB_PASSWORD
)
dbConn = mongoConn[MONGODB_DB]

dbConn["annotationData"].create_index("annotation.name")

dbConn["annotationData"].create_index("itemId")


dbConn["annotationData"].create_index([("itemId", 1), ("annotation.name", 1)])
