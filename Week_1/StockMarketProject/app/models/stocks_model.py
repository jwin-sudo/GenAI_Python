from pydantic import BaseModel
from typing import Optional

class StockModel(BaseModel):
    id: Optional[int] = None
    ticker: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    founded_year: Optional[int] = None

    
    
    model_config = {"from_attributes": True}

class StockCreateResponse(BaseModel):
    message: str
    stock: StockModel

    model_config = {"from_attributes": True}

