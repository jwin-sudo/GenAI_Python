from fastapi import FastAPI, HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from contextlib import asynccontextmanager
from starlette.middleware.cors import CORSMiddleware
from app.services.db_connection import Base, engine


from app.routers import users
from app.routers import items
from app.routers import chat
from app.routers import vector_ops
from app.routers import langgraph_ops
from app.routers import sql_ops

Base.metadata.create_all(bind=engine)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow all origins (not recommended for production)
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

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
app.include_router(langgraph_ops.router)
app.include_router(sql_ops.router)

# Generic sample endpoint (GET request that just returns a message)
@app.get("/")
async def sample_endpoint():
    return {"message": "Hello, FastAPI!"}

