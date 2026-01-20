from fastapi import FastAPI, HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from contextlib import asynccontextmanager
from app.services.vectordb_service import init_vector_store

from app.routers import users
from app.routers import items
from app.routers import chat
from app.routers import vector_ops



app = FastAPI()

#Setting CORS (Cross Origin Resource Sharing) policy 
origins = ["*"] # Allow all origins (not recommended for production)
origins = ["http://localhost"] # Allow requests only from localhost 

#TODO for Ben: CORS middleware

# Global custom Exception Handler 
# All Exceptions raised in the routers get handled here
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request, exception: HTTPException):
    return JSONResponse(
        status_code=exception.status_code,
        content={"message": exception.detail},
    )
# Import routers here
app.include_router(users.router)
app.include_router(items.router)
app.include_router(chat.router)
app.include_router(vector_ops.router)

# Generic sample endpoint (GET request that just returns a message)
@app.get("/")
async def sample_endpoint():
    return {"message": "Hello, FastAPI!"}

