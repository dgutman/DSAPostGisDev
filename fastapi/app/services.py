from sqlmodel import SQLModel, create_engine
from .models import *

DATABASE_URL = "postgresql://docker:docker@postgisdb/dsagis"

engine = create_engine(DATABASE_URL)
# with engine.connect() as con:
#     # connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
#     print(dir(con))
#     con.execute("CREATE EXTENSION IF NOT EXISTS vector")
### TO DO IS FIGURE OUT HOW TO MAKE THIS A PARAMETER
print("Creating DB and Tables")


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
