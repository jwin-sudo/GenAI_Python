from fastapi import FastAPI
from app.routers import stocks, price
from app.db import init_models
from app.auth import router as auth_router

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await init_models()

app.include_router(stocks.route)
app.include_router(price.route)
app.include_router(auth_router)
