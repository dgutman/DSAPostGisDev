from sqlmodel import SQLModel, create_engine
from .models import *
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://docker:docker@postgisdb/dsagis"

engine = create_engine(DATABASE_URL)
print("Creating DB and Tables")

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_db_and_tables():
    with SessionLocal() as session:
        print("Trying to enable vector extension")
        session.execute("CREATE EXTENSION IF NOT EXISTS vector")
        print("Vector Extension is enabled")
    SQLModel.metadata.create_all(engine)
