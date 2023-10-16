## Do all login and DB stuff in here to make imports not a nightmare...
import girder_client, os
from dotenv import load_dotenv
import pymongo

DSAKEY = os.getenv("DSAKEY")
DSA_BASE_URL = "https://megabrain.neurology.emory.edu/api/v1"

gc = girder_client.GirderClient(apiUrl=DSA_BASE_URL)
if DSAKEY:
    gc.authenticate(apiKey=DSAKEY)


## MONGO CONNECTION INFORMATION

MONGO_URI = "localhost:37017"
MONGODB_USERNAME = "docker"
MONGODB_PASSWORD = "docker"
MONGODB_HOST = "localhost"
MONGODB_PORT = 37017
MONGODB_DB = "cacheDSAannotationData"
APP_IN_DOCKER = False


### Create mongo connection strings here as well
mongoConn = pymongo.MongoClient(
    MONGO_URI, username=MONGODB_USERNAME, password=MONGODB_PASSWORD
)
dbConn = mongoConn[MONGODB_DB]
