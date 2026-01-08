from pydantic import BaseModel, Field
from typing import Annotated, Optional
# Check user_model for relevant notes 

class ItemModel(BaseModel):
    id: Annotated[int, Field(gt=0)] = None
    name: Annotated[str, Field(min_length=3, max_length=50)]
    description: Annotated[str, Field(min_length=10, max_length=100)]
    inventory: Annotated[int, Field(ge=0)] 
    # ge = greater than or equal to 
    # lt = less than 
    price: Annotated[float, Field(gt=0)]



    