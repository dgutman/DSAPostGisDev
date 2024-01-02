from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Session, select
from geoalchemy2.elements import WKTElement
from geoalchemy2.functions import ST_Distance, ST_AsGeoJSON, ST_MakeEnvelope
from sqlalchemy.orm import load_only
from sqlalchemy import func, and_, delete, select
import numpy as np
import random, requests
import girder_client
from typing import List
from .utils import computeColorSimilarityForFeatureSet


from .services import engine, create_db_and_tables, SessionLocal
from .models import (
    SimpleRectangles,
    DSAImage,
    tileFeatures,
    featureExtractionParams,
    imageFeatureSets,
    NPfeatureSet,
    DSAFeatureSetFile,
    VandyCellFeatures,
)
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


sampleRecord = VandyCellFeatures(
    featureSetId=1,
    localFeatureId=1,
    UniqueID="ID-00-00-000001",
    Cell_Centroid_X=225.660305343511,
    Cell_Centroid_Y=2830.02290076336,
    Cell_Area=262.0,
    Percent_Epithelium=100.0,
    Percent_Stroma=0.0,
    Nuc_Area=107.0,
    Mem_Area=114.0,
    Cyt_Area=41.0,
    Stain_Marker_Embeddings=[
        0.0806113682693119,
        0.0886383951698557,
        1427.0,
        634.854961832061,
        4737.5,
        2146.84732824427,
        2826.0,
        486.202290076336,
        0.00294379670564434,
        0.0025090530500571,
        0.0,
        9.9236641221374,
        33.5,
        28.4809160305344,
        120.0,
        18.2404580152672,
        0.00215293712774511,
        0.0019923398137027,
        42.0,
        20.9580152671756,
        59.5,
        29.0229007633588,
        114.0,
        16.706106870229,
    ],
)


@app.post("/addTileFeatures")
async def post_tileFeatures(featureBatch: List[tileFeatures]):
    tileData = [tile_obj.dict() for tile_obj in featureBatch]
    with Session(engine) as session:
        session.bulk_insert_mappings(tileFeatures, tileData)
        session.commit()
    return "Tile Feature Data added"


from pydantic import BaseModel


class SampleCellData(BaseModel):
    name: str
    cellType: int


@app.post("/insertTestFeatures")
async def post_testFeatures(featureJson: SampleCellData):
    print(featureJson)


from sqlalchemy.dialects.postgresql import insert


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_vandyRecord_objectCount(db: Session, feature_set_id: int) -> int:
    with Session(engine) as session:
        record_count = (
            session.query(VandyCellFeatures)
            .filter(VandyCellFeatures.featureSetId == feature_set_id)
            .count()
        )
        return record_count
    # query = select(func.count()).where(VandyCellFeatures.featureSetId == feature_set_id)
    # record_count = db.exec(query).scalar()
    # print(record_count)
    # return record_count


#   with Session(engine) as session:
#         tileData = (
#             session.query(tileFeatures)
#             .filter(tileFeatures.ftxtract_id == ftxtract_id)
#             # .filter(tileFeatures.imageId == imageId)
#             .options(
#                 load_only(
#                     tileFeatures.imageId,
#                     tileFeatures.topX,
#                     tileFeatures.topY,
#                     tileFeatures.width,
#                     tileFeatures.height,
#                     tileFeatures.average,
#                     tileFeatures.localTileId,
#                 )
#             )
#             .limit(10000)
#             .all()
#         )
#         return tileData

#     return None


def update_object_count(feature_set_id: int, record_count: int) -> int:
    with Session(engine) as session:
        dsa_feature_set = (
            session.query(DSAFeatureSetFile)
            .filter(DSAFeatureSetFile.id == feature_set_id)
            .first()
        )
        dsa_feature_set.objectCount = record_count
        session.commit()
        session.refresh(dsa_feature_set)
        return dsa_feature_set.objectCount
    # dsa_feature_set = (
    #     db.exec(DSAFeatureSetFile)
    #     .filter(DSAFeatureSetFile.id == feature_set_id)
    #     .first()
    # )
    # dsa_feature_set.objectCount = record_count
    # db.commit()
    # db.refresh(dsa_feature_set)
    # return dsa_feature_set.objectCount


@app.post("/insertVandyCellFeatures")
async def insert_vandy_cell_features(vandy_features: List[VandyCellFeatures]):
    # Process and store the vandy_features in the database
    # Replace this with your actual database storage logic

    vandyCellData = [cell_obj.dict() for cell_obj in vandy_features]

    with Session(engine) as session:
        # stmt = insert(VandyCellFeatures).values(vandyCellData)
        # # stmt = stmt.on_conflict_do_nothing(constraint="idx_unique_cellObject")
        # stmt = stmt.on_conflict_do_nothing(
        #     index_elements=["featureSetId", "localFeatureId"]
        # )
        # session.exec(stmt)
        # session.commit()
        # return len(vandy_features), "Inserted sample record"

        result = session.bulk_insert_mappings(VandyCellFeatures, vandyCellData)
        # # session._bulk_save_mappings(vandy_features, return_defaults=True)
        # # for feature in vandy_features:
        # #     session.add(feature)
        # print("About to insert", len(vandy_features), "records")
        session.commit()
        # inserted_count = result.rowcount
        # print("Successfully inserted", inserted_count, "records")
        # return {"inserted_count": inserted_count, "records_sent": len(vandy_features)}

        # #     session.bulk_insert_mappings(VandyCellFeatures, cellData)
        #     session.commit()

        # Store the feature in the database
        # Example: feature.save_to_database()

    return {"message": "VandyCellFeatures inserted successfully"}


# @app.post("/insertVandyCellFeatures")
# async def post_vandyFeatures(vandyFeatureBatch: List[VandyCellFeatures]):
#     print(len(vandyFeatureBatch), "Records were received")
#     # cellData = [cell_obj.model_dump() for cell_obj in vandyFeatureBatch]
#     # with Session(engine) as session:
#     #     session.add(sampleRecord)
#     #     session.commit()
#     #     return "Inserted sample record"
#     #     session.bulk_insert_mappings(VandyCellFeatures, cellData)
#     #     session.commit()
#     # return "Cell Feature Data added"


@app.put("/update-featureSetFile-objectCount/{feature_set_id}")
def update_object_count(
    feature_set_id: int, db: Session = Depends(get_db)
):  # , db: Session = Depends(get_db)):
    # Get the count of records in the VandyCellFeatures table for the given featureSetId
    record_count = get_vandyRecord_objectCount(db, feature_set_id)

    # Update the objectCount field in the DSAFeatureSetFile table
    updated_count = update_object_count(db, feature_set_id, record_count)

    return {
        "message": "Object count updated successfully",
        "updated_count": updated_count,
    }


@app.delete("/deleteTileFeatures")
async def delete_tileFeatures(imageId: str, ftxtract_id: int):
    """This will delete tiles associated with an image in case I want to regenerate them"""
    with Session(engine) as session:
        statement = (
            delete(tileFeatures)
            .where(tileFeatures.imageId == imageId)
            .where(tileFeatures.ftxtract_id == ftxtract_id)
        )
        result = session.exec(statement)
        session.commit()
        # print(result.rowcount)
        return "Tile Feature Data Truncated  "  # % result.rowCount


## TO DO: Add optinoal parameter that will return all fields, not just the ones listed below
@app.get("/getTileFeatures")
async def get_tileFeatures(ftxtract_id: int):
    # print("Getting tile features based on internal imageId")

    with Session(engine) as session:
        tileData = (
            session.query(tileFeatures)
            .filter(tileFeatures.ftxtract_id == ftxtract_id)
            # .filter(tileFeatures.imageId == imageId)
            .options(
                load_only(
                    tileFeatures.imageId,
                    tileFeatures.topX,
                    tileFeatures.topY,
                    tileFeatures.width,
                    tileFeatures.height,
                    tileFeatures.average,
                    tileFeatures.localTileId,
                )
            )
            .limit(10000)
            .all()
        )
        return tileData

    return None


@app.get("/getNPfeatures")
async def get_NPfeatures(imageFeatureSet_id: int):
    # print("Getting tile features based on internal imageId")

    with Session(engine) as session:
        NPfeatureData = (
            session.query(NPfeatureSet)
            .filter(NPfeatureSet.imageFeatureSet_id == imageFeatureSet_id)
            # .filter(tileFeatures.imageId == imageId)
            # .options(
            #     load_only(
            #         tileFeatures.imageId,
            #         tileFeatures.topX,
            #         tileFeatures.topY,
            #         tileFeatures.width,
            #         tileFeatures.height,
            #         tileFeatures.average,
            #         tileFeatures.localTileId,
            #     )
            # )
            .limit(10000)
            .all()
        )
        return NPfeatureData

    return None


@app.get("/getFeatureSets")
async def get_featureSets(
    imageId: str,
):  # , featureType: str, imageFeatureSet_id: int):
    ### Get all the feature sets available for a given image
    # if featureType == "nftFeature":
    #     with Session(engine) as session:
    #         nftFeatureSet = session.query(NPfeatureSet).filter(NPfeatureSet.imageFeatureSet_id == imageFeatureSet_id)
    #         return None
    with Session(engine) as session:
        featureSets = (
            session.query(imageFeatureSets)
            .filter(imageFeatureSets.imageId == imageId)
            .all()
        )

        return featureSets
    return None


@app.get("/computeFeatureDistance")
async def get_computeFeatureDistance(
    ftxtract_id: int, distanceThresh: float, refFeatureId: str
):
    ### Given a ftxtract_id and a reference vector, and a distance
    ### Compute which tiles (or features) are within the defined metric
    with Session(engine) as session:
        featureSelectedData = (
            session.query(tileFeatures)
            .filter(tileFeatures.ftxtract_id == ftxtract_id)
            .options(
                load_only(
                    tileFeatures.imageId, tileFeatures.localTileId, tileFeatures.average
                )
            )
            .all()
        )

        refFeatureVector = (
            session.query(tileFeatures)
            .filter(tileFeatures.ftxtract_id == ftxtract_id)
            .filter(tileFeatures.localTileId == refFeatureId)
            .options(load_only(tileFeatures.average))
            .first()
        )
        ftrDistances = computeColorSimilarityForFeatureSet(
            featureSelectedData, refFeatureVector.average, distanceThresh
        )
        return ftrDistances
    return None


@app.post("/addFeatureExtractionParams")
async def insert_featureExtractionParams(featXtractParams: featureExtractionParams):
    print("Adding parameters used to do a certain tile feature extraction")
    with Session(engine) as session:
        exist = (
            session.query(featureExtractionParams)
            .filter(featureExtractionParams.imageId == featXtractParams.imageId)
            .filter(featureExtractionParams.tileWidth == featXtractParams.tileWidth)
            .filter(
                featureExtractionParams.magnification == featXtractParams.magnification
            )
            .first()
        )
        if exist:
            return exist
        else:
            ftr = session.add(featXtractParams)
            session.commit()
            session.refresh(featXtractParams)
            return featXtractParams  ## This should return a fresh copy of the extracted feature..

    return None


@app.post("/lookupFeatureExtractionParams")
async def lookup_featureExtractionParams(
    imageId: str, magnification: float, tileSizeParam: str
):
    print(
        "This will determine if a set of feature extractions have already been run at this resolution"
    )
    with Session(engine) as session:
        exist = (
            session.query(featureExtractionParams)
            .filter(featureExtractionParams.imageId == imageId)
            .filter(featureExtractionParams.tileSizeParam == tileSizeParam)
            .filter(featureExtractionParams.magnification == magnification)
            .first()
        )
        if exist:
            return exist
        else:
            return None
    return None


@app.post("/getFeatureSetId")
async def get_featureSetId(imageId: str, magnification: float, tileSizeParam: str):
    print(
        "This will determine if a set of feature extractions have already been run at this resolution"
    )
    with Session(engine) as session:
        exist = (
            session.query(featureExtractionParams)
            .filter(featureExtractionParams.imageId == imageId)
            .filter(featureExtractionParams.tileSizeParam == tileSizeParam)
            .filter(featureExtractionParams.magnification == magnification)
            .first()
        )
        if exist:
            return exist
        else:
            return None
    return None


## Do I add an imageId mechanism as well... hmmm..


@app.get("/lookupImage")
async def lookupImage(imageName: str, dsaApiUrl: str):
    with Session(engine) as session:
        print(imageName)
        imageInfo = (
            session.exec(DSAImage).filter(DSAImage.imageName == imageName).first()
        )
        # return imageInfo
        return imageInfo


@app.get("/lookupImageById")
async def lookupImage(imageId: str, dsaApiUrl: str):
    with Session(engine) as session:
        # print(imageName)
        imageInfo = session.exec(DSAImage).filter(DSAImage.imageId == imageId).first()
        return imageInfo


@app.get("/lookupFeatureSetFile")
async def lookupFeatureSetFile(dsaFileId: str, dsaApiUrl: str):
    with Session(engine) as session:
        localFeatureSetFileInfo = (
            session.exec(DSAFeatureSetFile)
            .filter(DSAFeatureSetFile.dsaFileId == dsaFileId)
            .first()
        )
        # # return imageInfo
        return localFeatureSetFileInfo


@app.post("/insertFeatureSetFile")
async def insertFeatureSetFile(featureSetFileInfo: DSAFeatureSetFile):
    print(featureSetFileInfo, "was received from the client")

    with Session(engine) as session:
        exist = (
            session.query(DSAFeatureSetFile)
            .filter(DSAFeatureSetFile.dsaFileId == featureSetFileInfo.dsaFileId)
            .first()
        )
        if exist:
            return exist
        else:
            session.add(featureSetFileInfo)
            session.commit()
            session.refresh(featureSetFileInfo)
            return featureSetFileInfo  ## This should return a fresh copy of the extracted feature..


@app.post("/add-DSAImage/")
async def add_DSAImage(imageId: str, dsaApiUrl: str):
    with Session(engine) as session:
        exist = session.query(DSAImage).filter(DSAImage.imageId == imageId).first()
        ## Not sure if I want to throw an error if the item exists already
        ## May also want to eventually allow items to be updated if forced.

        if not exist:
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
        else:
            return exist

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

# @app.post("/add-station/")
# async def add_station(station: Stations):
#     with Session(engine) as session:
#         exist = (
#             session.query(Stations)
#             .filter(Stations.station_id == station.station_id)
#             .first()
#         )
#         if exist:
#             raise HTTPException(status_code=400, detail="Station already exists")

#         point = f"POINT({station.longitude} {station.latitude})"
#         station.geom = WKTElement(point, srid=4326)

#         session.add(station)
#         session.commit()
#         session.refresh(station)

#         to_return = {}
#         to_return["station_id"] = station.station_id
#         to_return["latitude"] = station.latitude
#         to_return["longitude"] = station.longitude
#         to_return["cp"] = station.cp
#         to_return["city"] = station.city
#         to_return["address"] = station.adress

#         return to_return

# from sqlalchemy.dialects.postgresql import insert

# stmt = insert(User).values(
#     [
#         dict(name="sandy", fullname="Sandy Cheeks"),
#         dict(name="squidward", fullname="Squidward Tentacles"),
#         dict(name="spongebob", fullname="Spongebob Squarepants"),
#     ]
# )

# stmt = stmt.on_conflict_do_update(
#     index_elements=[User.name], set_=dict(fullname=stmt.excluded.fullname)
# ).returning(User)

# orm_stmt = select(User).from_statement(stmt).execution_options(populate_existing=True)
# for user in session.execute(
#     orm_stmt,
# ).scalars():
#     print("inserted or updated: %s" % user)
