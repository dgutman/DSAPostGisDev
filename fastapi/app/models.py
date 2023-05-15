from typing import Optional
from sqlmodel import Field, SQLModel, Integer, Float
from datetime import datetime
from sqlalchemy import Column, BigInteger
from geoalchemy2.types import Geometry
from typing import Any, List, Optional


class DSAImage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    apiURL: str
    imageId: str
    imageName: str
    levels: int
    magnification: float
    mm_x: float
    mm_y: float
    sizeX: int
    sizeY: int
    tileWidth: int
    tileHeight: int


from sqlalchemy.dialects import (
    postgresql,
)  # ARRAY contains requires dialect specific type


class tileFeatures(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    apiURL: str
    imageId: str = Field(index=True)
    imageName: str
    topX: int
    topY: int
    width: int
    height: int
    featureType: str  ### Should be something like imgHistogram
    ftxtract_id: int
    localTileId: str  ## This is most likely the tilePosition in the current run
    red: Optional[List[int]] = Field(
        default=None, sa_column=Column(postgresql.ARRAY(Integer()))
    )
    green: Optional[List[int]] = Field(
        default=None, sa_column=Column(postgresql.ARRAY(Integer()))
    )
    blue: Optional[List[int]] = Field(
        default=None, sa_column=Column(postgresql.ARRAY(Integer()))
    )
    average: Optional[List[float]] = Field(
        default=None, sa_column=Column(postgresql.ARRAY(Float()))
    )

    # Needed for Column(JSON)
    class Config:
        arbitrary_types_allowed = True


class SimpleRectangles(SQLModel, table=True):
    rectangle_id: int = Field(primary_key=True)
    slide_id: str
    x1: int
    x2: int
    y1: int
    y2: int
    shapeName: str
    shapeLabel: str
    shapeLocation: Optional[Any] = Field(sa_column=Column(Geometry("GEOMETRY")))


class MoreSimpleRectangles(SQLModel, table=True):
    rectangle_id: int = Field(primary_key=True)
    slide_id: str
    x1: int
    x2: int
    y1: int
    y2: int
    shapeName: str
    shapeLabel: str
    shapeLocation: Optional[Any] = Field(sa_column=Column(Geometry("GEOMETRY")))


class featureExtractionParams(SQLModel, table=True):
    ftxtract_id: int = Field(primary_key=True, default=None)
    tileWidth: int
    tileHeight: int
    featureType: str
    ftxComputeTime: float
    bytesRead: Optional[int] = Field(sa_column=Column(BigInteger()), default=None)
    imageId: str
    tilesProcessed: int
    sizeX: int
    sizeY: int
    magnification: float
    tileSizeParam: Optional[str] = Field(default=None)
    ## This helps me keep track of if I used a native tile sizing or multiple threreof

    # {'imageName': 'TCGA-19-1787-01C-01-TS1.b9f6f0f2-14f2-4bc5-b7f8-9520ec38eb98.svs',


# 'imagePath': 'SmallSampleFiles/TCGA-19-1787-01C-01-TS1.b9f6f0f2-14f2-4bc5-b7f8-9520ec38eb98.svs',
# 'opType': 'tileHist', 'startTime': 1683232143.5455363,
# 'elapsedTime': 0.13014698028564453, 'tilesProcessed': 4,
# 'tileWidth': 256, 'tileHeight': 256, 'sizeX': 6000,
#  'sizeY': 7977, 'bytesRead': 747000, 'magnification': 1.25,
# 'tileSizeParam': 'native'}

#     tags: Optional[Set[str]] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))

# (...)
#         tagged = session.query(Item).filter(Item.tags.contains([tag]))

# from sqlmodel import Field, Session, SQLModel, create_engine, JSON, Column


# class Block(SQLModel, table=True):
#     id: int = Field(..., primary_key=True)
#     values: List[str] = Field(sa_column=Column(JSON))

#     # Needed for Column(JSON)
#     class Config:
#         arbitrary_types_allowed = True


# engine = create_engine("sqlite:///test_database.db", echo=True)

# SQLModel.metadata.create_all(engine)

# b = Block(id=0, values=['test', 'test2'])
# with Session(engine) as session:
#     session.add(b)
#     session.commit()

# class Stations(SQLModel, table=True):
#     station_id: str = Field(primary_key=True)
#     latitude: float
#     longitude: float
#     cp: str
#     city: str
#     adress: str
#     geom: Optional[Any] = Field(sa_column=Column(Geometry("GEOMETRY")))


# class Cities(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     postal_code: str
#     name: str
#     lat: float
#     lon: float


# class GasPrices(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     station_id: str
#     oil_id: str
#     nom: str
#     valeur: float
#     maj: datetime = Field(default_factory=datetime.utcnow)
