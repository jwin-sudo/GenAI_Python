from typing import Annotated

from pydantic import BaseModel, Field, conint, constr
# This MODEL class helps us MODEL data that we'll use throughout the app

# Notice the use of data types conint and constr
# They help us enforce constraints (or rules) on the data

class UserModel(BaseModel):
    id: Annotated[int, Field(gt=0)] # t means "greater than" 0
    username: Annotated[str, Field(min_length=3)]
    password: Annotated[str, Field(min_length=8)]
    email: Annotated[str, Field(min_length=8)]


