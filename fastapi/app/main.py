from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from sqlmodel import Session
from geoalchemy2.elements import WKTElement
from geoalchemy2.functions import ST_Distance, ST_AsGeoJSON, ST_MakeEnvelope
from sqlalchemy import func, and_, delete
import numpy as np
import random, requests
import girder_client
from typing import List

from .services import engine, create_db_and_tables
from .models import Cities, Stations, GasPrices, SimpleRectangles, DSAImage, tileFeatures
from .utils import extend_dict, pretify_address

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/add-station/")
async def add_station(station: Stations):
    with Session(engine) as session:
        exist = session.query(Stations).filter(Stations.station_id == station.station_id).first()
        if exist:
            raise HTTPException(status_code=400, detail="Station already exists")

        point = f"POINT({station.longitude} {station.latitude})"
        station.geom = WKTElement(point, srid=4326)

        session.add(station)
        session.commit()
        session.refresh(station)

        to_return = {}
        to_return["station_id"] = station.station_id
        to_return["latitude"] = station.latitude
        to_return["longitude"] = station.longitude
        to_return["cp"] = station.cp
        to_return["city"] = station.city
        to_return["adress"] = station.adress

        return to_return


@app.post("/addTileFeatures")
async def post_tileFeatures(featureBatch: List[tileFeatures]):
    tileData = [tile_obj.dict() for tile_obj in featureBatch]
    with Session(engine) as session:
        session.bulk_insert_mappings(tileFeatures, tileData)
        session.commit()
    return "Tile Feature Data added"


@app.delete("/deleteTileFeatures")
async def delete_tileFeatures():
    """This will delete tiles associated with an image in case I want to regenerate them"""
    with Session(engine) as session:
        statement = delete(tileFeatures)
        result = session.exec(statement)
        session.commit()
        # print(result.rowcount)
        return "Tile Feature Data Truncated  "  # % result.rowCount


@app.get("/getTileFeatures")
async def get_tileFeatures():
    print("Getting tile features")
    with Session(engine) as session:
        tileData = session.query(tileFeatures).limit(50).all()
        return tileData

    return None


@app.get("/lookupImage")
async def lookupImage(imageName: str, dsaApiUrl: str):
    with Session(engine) as session:
        imageInfo = session.query(DSAImage).filter(DSAImage.imageName == imageName).first()
        # return imageInfo
        return imageInfo

    return None


@app.post("/add-DSAImage/")
async def add_DSAImage(imageId: str, dsaApiUrl: str):
    with Session(engine) as session:
        exist = session.query(DSAImage).filter(DSAImage.imageId == imageId).first()
        ## Not sure if I want to throw an error if the item exists already
        ## May also want to eventually allow items to be updated if forced.
        gc = girder_client.GirderClient(apiUrl=dsaApiUrl)
        ## Throw an exception if girder client fails.. add in the future

        try:
            ## TO DO ADD SOMETHING THAT MAKES SURE THE SERVER IS EVEN ACCESSIBLE...

            resp = requests.get(dsaApiUrl, timeout=1)
            ### Adding this to make sure server is accessible, otherwise this just hangs
            itemInfo = gc.get(f"item/{imageId}")
            tileData = gc.get(f"item/{imageId}/tiles")

            imageItem = DSAImage(
                imageName=itemInfo["name"],
                apiURL=dsaApiUrl,
                imageId=imageId,
                magnification=tileData["magnification"],
                mm_x=tileData["mm_x"],
                mm_y=tileData["mm_y"],
                sizeX=tileData["sizeX"],
                sizeY=tileData["sizeY"],
                levels=tileData["levels"],
                tileWidth=tileData["tileWidth"],
                tileHeight=tileData["tileHeight"],
            )

            session.add(imageItem)
            session.commit()
            session.refresh(imageItem)
            return imageItem

        except:
            print("Having an issue with one of the DSA servers")

    return None


@app.get("/insert_random_rects/")
async def gen_random_rects(slide_id: str):
    ### Let's generate 500 random shapes...
    numShapesToGen = 5
    max_X = 10000
    max_Y = 10000
    boxSize_X = 40
    boxSixe_Y = 50

    with Session(engine) as session:
        for i in range(numShapesToGen):
            x1 = random.randrange(0, max_X)
            y1 = random.randrange(0, max_Y)

            x2 = x1 + boxSize_X
            y2 = y1 + boxSixe_Y

            myRect = SimpleRectangles(
                slide_id=slide_id,
                x1=x1,
                x2=x2,
                y1=y1,
                y2=y2,
                shapeName="box",
                shapeLabel="NFT",
                shapeLocation=ST_MakeEnvelope(x1, y1, x2, y2, 4326),
            )
            session.add(myRect)
        session.commit()
        ##Insert statement values would be..
        #     valList = f"({slide_id},{x1},{x2},{y1},{y2},'box','NFT', ST_MakeEnvelope({x1},{y1},{x2},{y2},4326))"
    return "Mission Accomplished"


@app.get("/rectangles/")
async def get_rectangles():
    with Session(engine) as session:
        rectangle = session.query(SimpleRectangles).all()
        rectSet = [r for r in rectangle]
        print(len(rectSet))
        print(rectSet[0])
        return len(rectSet)


@app.get("/getImageList/")
async def get_imageList():
    with Session(engine) as session:
        images = session.query(DSAImage).all()
        print(len(images))
        return images


# @app.get("/stations/")
# async def get_prices(oil_type: str, postal_code: str):
#     with Session(engine) as session:
#         city = session.query(Cities).filter(Cities.postal_code == postal_code).first()
#         if not city:
#             raise HTTPException(status_code=404, detail="Postal Code not found")
#         stations = (
#             session.query(
#                 Stations.station_id,
#                 Stations.adress,
#                 Stations.cp,
#                 Stations.city,
#                 Stations.latitude,
#                 Stations.longitude,
#             )
#             .filter(
#                 ST_Distance(
#                     Stations.geom.ST_GeogFromWKB(),
#                     WKTElement(f"POINT({city.lon} {city.lat})", srid=4326).ST_GeogFromWKB(),
#                 )
#                 < 30000
#             )
#             .subquery()
#         )

#         price_wanted_gas = session.query(GasPrices).filter(GasPrices.nom == oil_type).subquery()

#         last_price = (
#             session.query(price_wanted_gas.c.station_id, func.max(price_wanted_gas.c.maj).label("max_maj"))
#             .group_by(price_wanted_gas.c.station_id)
#             .subquery()
#         )

#         last_price_full = (
#             session.query(price_wanted_gas)
#             .join(
#                 last_price,
#                 and_(
#                     price_wanted_gas.c.station_id == last_price.c.station_id,
#                     price_wanted_gas.c.maj == last_price.c.max_maj,
#                 ),
#             )
#             .subquery()
#         )

#         stations_with_price = (
#             session.query(stations, last_price_full)
#             .join(last_price_full, stations.c.station_id == last_price_full.c.station_id)
#             .all()
#         )

#         prices = [float(e["valeur"]) for e in stations_with_price]
#         avg_price = float(np.median(prices))

#         output = {
#             "lat": city.lat,
#             "lon": city.lon,
#             "city": pretify_address(city.name),
#             "station_infos": sorted(
#                 [extend_dict(x, avg_price, city.lat, city.lon) for x in stations_with_price],
#                 key=lambda x: -(x["delta_average"]),
#             ),
#         }

#         return output

# @app.post("/add-gas-price/")
# async def add_station(gasPrice: GasPrices):
#     with Session(engine) as session:
#         exist = (
#             session.query(GasPrices)
#             .filter(GasPrices.station_id == gasPrice.station_id)
#             .filter(GasPrices.oil_id == gasPrice.oil_id)
#             .filter(GasPrices.nom == gasPrice.nom)
#             .filter(GasPrices.valeur == gasPrice.valeur)
#             .filter(GasPrices.maj == gasPrice.maj)
#             .first()
#         )
#         if exist:
#             raise HTTPException(status_code=400, detail="Entry already exists")

#         session.add(gasPrice)
#         session.commit()
#         session.refresh(gasPrice)
#         return gasPrice

# @app.post("/add-city/")
# async def add_city(city: Cities):
#     with Session(engine) as session:
#         exist = session.query(Cities).filter(Cities.postal_code == city.postal_code).first()
#         print(exist)
#         if exist:
#             raise HTTPException(status_code=400, detail="Postal code already exists")

#         session.add(city)
#         session.commit()
#         session.refresh(city)
#         return city
