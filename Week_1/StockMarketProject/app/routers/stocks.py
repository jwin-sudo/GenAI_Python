from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import yfinance as yf

from app.models.stocks_model import StockModel, StockCreateResponse
from app.models.quote_model import QuoteModel
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

@route.get("/{symbol}", response_model=QuoteModel)
async def get_stock_quote(symbol: str, session: AsyncSession = Depends(get_session)):
    # ensure stock exists in DB
    q = await session.execute(select(StockORM).where(StockORM.ticker == symbol))
    stock = q.scalars().first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    # fetch latest intraday data from yfinance in thread (sync lib)
    def fetch_latest(sym: str):
        t = yf.Ticker(sym)
        # try intraday history first
        try:
            hist = t.history(period="1d", interval="1m")
            if not hist.empty:
                last = hist.iloc[-1]
                return {
                    "open": float(last["Open"]),
                    "high": float(last["High"]),
                    "low": float(last["Low"]),
                    "close": float(last["Close"]),
                    "volume": int(last["Volume"]),
                }
        except Exception:
            pass
        # fallback to slower info / fast_info
        try:
            fi = getattr(t, "fast_info", None) or {}
            return {
                "open": float(fi.get("open", 0)) if fi else None,
                "high": float(fi.get("dayHigh", 0)) if fi else None,
                "low": float(fi.get("dayLow", 0)) if fi else None,
                "close": float(fi.get("lastPrice", 0)) if fi else None,
                "volume": int(fi.get("lastVolume", 0)) if fi else None,
            }
        except Exception:
            return {"open": None, "high": None, "low": None, "close": None, "volume": None}

    loop = asyncio.get_running_loop()
    quote = await loop.run_in_executor(None, fetch_latest, symbol)

    return QuoteModel(
        ticker=stock.ticker,
        company_name=getattr(stock, "company_name", None),
        open=quote.get("open"),
        high=quote.get("high"),
        low=quote.get("low"),
        close=quote.get("close"),
        volume=quote.get("volume"),
    )

