# 3 Classes in this file:
    # UserDBModel - represents a user in the database (a record in the "users" table)
    # CreateUserModel - represents what the user passes in to create a new user
    # ReadUserModel - represents what we return to the user when we send user data
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String

from app.services.db_connection import Base

# This is the Class that defines and builds the Table in the DB
class UserDBModel(Base):
    __tablename__ = "users" # Name the table in the DB

    # Define the table columns
    id = Column(Integer, primary_key=True) # Setting as primary key autoincrements this field
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)

# This Model is used when CREATING (POSTing) a new user
class CreateUserModel(BaseModel):
    username:str # Skipping the constraints - you can check our other models for examples
    password:str
    email:str

# This Model is used when READING (GETting) user data
class ReadUserModel(BaseModel):
    id:int
    username:str
    email:str

# TODO: Maybe a model for update?
# TODO: (maybe has every field? get user by id then update with whatever's new)

""" 
Why make separate models for user input/output?
We don't HAVE to... but it's good to have explicit models for each "form" of the data
When we create a new user, we don't need their ID
When we read user data, we want the full spectrum of data EXCEPT the password

Alsoooo... We can't just use the DB model for FastAPI Routers
Recall that routes only accept primitives and Pydantic models
So our class xyz(Base) won't work in a route. we need class xyz(BaseModel)
"""