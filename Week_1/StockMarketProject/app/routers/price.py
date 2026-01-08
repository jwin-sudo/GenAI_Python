from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price_model import PriceModel, PriceCreateResponse
from app.models.stocks_model import StockModel, StockCreateResponse

from app.db import get_session
from app.db_models import Price as PriceORM
from app.db_models import Stock as StockORM

route = APIRouter(
    prefix="/price",
    tags=["prices"]
)

@route.post("/", response_model=PriceCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_stock_price(stock_price: PriceModel, session: AsyncSession = Depends(get_session)):
    q = await session.execute(select(PriceORM).where(PriceORM.ticker == stock_price.ticker))
    if q.scalars().first():
        raise HTTPException(status_code=400, detail="Ticker already exists")
    
    new = PriceORM(ticker=stock_price.ticker, high=stock_price.high, low=stock_price.low)
    session.add(new)
    await session.commit()
    await session.refresh(new)
    return {
        "message": "Stock price created successfully",
        "stock": PriceModel.from_orm(new)
    }

@route.get("/{ticker}", response_model= PriceCreateResponse)
async def get_ticker_price(ticker = str, session: AsyncSession = Depends(get_session)):
    stock_q = await session.execute(select(StockORM).where(StockORM.ticker == ticker))
    stock = stock_q.scalars().first()

    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    price_q = await session.execute(select(PriceORM).where(PriceORM.ticker == ticker))
    price = price_q.scalars().first()
    
    if not price:
        raise HTTPException(status_code=404, detail="Price not found for the given ticker")
    else:
        return {
            "message": "Stock price retrieved successfully",
            "stock": PriceModel.from_orm(price)
        }
