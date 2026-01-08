from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stocks_model import StockModel, StockCreateResponse
from app.db import get_session
from app.db_models import Stock as StockORM

route = APIRouter(
    prefix="/stocks",
    tags=["stocks"]
)

@route.post("/", response_model=StockCreateResponse, status_code=201)
async def create_stocks(stock: StockModel, session: AsyncSession = Depends(get_session)):
    q = await session.execute(select(StockORM).where(StockORM.ticker == stock.ticker))
    if q.scalars().first():
        raise HTTPException(status_code=400, detail="Ticker already exists")
    
    new = StockORM(ticker=stock.ticker, company_name=stock.company_name, sector=stock.sector, founded_year=stock.founded_year)
    session.add(new)
    await session.commit()
    await session.refresh(new)
    return {
        "message": "Stock created successfully",
        "stock": StockModel.from_orm(new)
    }

 