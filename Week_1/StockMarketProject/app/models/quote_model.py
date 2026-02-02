from typing import Optional
from pydantic import BaseModel

class QuoteModel(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None