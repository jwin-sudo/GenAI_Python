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

@route.post("/", response_model=StockCreateResponse, status_code=status.HTTP_201_CREATED)
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

@route.get("/", response_model=List[StockCreateResponse])
async def get_all_stocks(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(StockORM))
    stocks = result.scalars().all()
    return [
        {"message": "Stock retrieved",
         "stock": StockModel.from_orm(stock)}
         for stock in stocks
    ]


@route.put("/{stock_id}", response_model=StockCreateResponse)
async def update_stock(stock_id: int, stock: StockModel, session: AsyncSession = Depends(get_session)):
    q = await session.execute(select(StockORM).where(StockORM.id == stock_id))
    existing_stock = q.scalars().first()
    if not existing_stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    existing_stock.ticker = stock.ticker
    existing_stock.company_name = stock.company_name
    existing_stock.sector = stock.sector
    existing_stock.founded_year = stock.founded_year

    session.add(existing_stock)
    await session.commit()
    await session.refresh(existing_stock)
    return {
        "message": "Stock updated successfully",
        "stock": StockModel.from_orm(existing_stock)
    }

@route.delete("/{stock_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stock(stock_id: int, session: AsyncSession = Depends(get_session)):
    q = await session.execute(select(StockORM).where(StockORM.id == stock_id))
    existing_stock = q.scalars().first()
    if not existing_stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    await session.delete(existing_stock)
    await session.commit()
    return

@route.get("/some_stocks", response_model=List[StockModel])
async def get_some_stocks(year, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(StockORM).where(StockORM.founded_year >= year))
    stocks = result.scalars().all()
    return [StockModel.from_orm(stock) for stock in stocks]

@route.patch("/{stock_id}/update_sector/{new_sector}", response_model=StockCreateResponse)
async def update_stock_sector(stock_id: int, new_sector: str, session: AsyncSession = Depends(get_session)):
    q = await session.execute(select(StockORM).where(StockORM.id == stock_id))
    existing_stock = q.scalars().first()
    if not existing_stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    existing_stock.sector = new_sector
    session.add(existing_stock)
    await session.commit()
    await session.refresh(existing_stock)
    return {
        "message": "Stock sector updated successfully",
        "stock": StockModel.from_orm(existing_stock)
    }

