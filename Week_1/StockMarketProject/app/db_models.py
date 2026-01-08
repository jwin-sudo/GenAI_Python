from sqlalchemy import Column, Integer, String, Float
from app.db import Base

class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticker = Column(String(20), unique=True, nullable=False)
    company_name = Column(String(255), nullable=False)
    sector = Column(String(100), nullable=False)
    founded_year = Column(Integer, nullable=False)

class Price(Base):
    __tablename__ = "stock_price"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticker = Column(String(20), unique=True, nullable=False)
    high = Column(Integer, nullable=False)
    low = Column(Integer, nullable=False)