from pydantic import BaseModel
from typing import Optional

class PriceModel(BaseModel):
    id: Optional[int] = None
    ticker: str
    high: int
    low: int

    
    
    model_config = {"from_attributes": True}

class PriceCreateResponse(BaseModel):
    message: str
    stock: PriceModel

    model_config = {"from_attributes": True}
