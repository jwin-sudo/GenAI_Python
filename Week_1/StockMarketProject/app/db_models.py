from sqlalchemy import Column, Integer, String, Float
from app.db import Base

class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticker = Column(String(20), unique=True, nullable=False)
    company_name = Column(String(255), nullable=True)
    sector = Column(String(100), nullable=True)
    founded_year = Column(Integer, nullable=True)


