from fastapi import FastAPI
from app.routers import stocks
from app.db import init_models

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await init_models()

app.include_router(stocks.route)
