# Define the DB URL (where the Database lives in our system)
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_URL = "sqlite:///./app.db" # DB will live in the app directory

# Create the engine that will connect to the DB
engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread":False} # allows concurrent requests (DB requests at the same time)
)

# Define the Session which will let us interact with the DB
LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
"""
-autocommit = False: Commit DB transactions manually (safer, more control)
-autoflush = False: Don't automatically flush changes. 
What is flush? to flush a DB is to sync it with the state of the session
-bind=engine: Links this session to our specific DB engine
"""


# A function that returns DB connections (we'll import this wherever needed)
def get_db():
    db = LocalSession() # Create a new session instance
    try:
        yield db # yield? this just means we're sending the DB to the caller indefinitely
    # TODO: could have an except block to catch any kinds of DB-related exceptions
    finally:
        db.close() # Close the connection when done, prevent memory leaks


# Lastly, define a Base class for our DB models to inherit from
Base = declarative_base()