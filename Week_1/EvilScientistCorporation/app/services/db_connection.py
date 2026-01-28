# Define the DB URL (where the Database lives in our system)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DB_URL = "sqlite:///./app.db"

# Create the engine that will connect to the DB 
engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False} # Needed for SQLite to allow multi-threading
)

# Define the Session which will let us interact with the DB
LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
"""
-autocommit = False: Commit DB transactions manually (safer, more control)
-autoflush = False: Don't automatically flush changes.
What is flush? to flush a DB is to sync it with the state of the session 
-bind=engine: Links this session to our specific DB engine 
"""
# a function that returns DB connections (we'lll import this wherever needed)
def get_db():
    db = LocalSession() # Create a new session instance 
    try:
        yield db # yield? this just means we're sending the DB to the caller indefinitely 

    # TODO: could have an except block to catch any kinds of DB-related exceptions

    finally:
        db.close() # Ensure the DB session is closed after use

# Lastly, define a Base class 
Base = declarative_base()