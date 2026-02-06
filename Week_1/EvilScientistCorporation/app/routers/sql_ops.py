
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.user_db_model import CreateUserModel, UserDBModel
from app.services.chain_service import get_general_chain
from app.services.db_connection import get_db

# This is a router just like any other, but it interacts with a SQlite DB

# 3 methods - create user, get all users, then RAG LLM invocation with user data

router = APIRouter(
    prefix="/sql",
    tags=["sql"]
)

# Create User
@router.post("/")
async def create_user(incoming_user: CreateUserModel, db: Session = Depends(get_db)):

    # TODO: a uniqueness check and other validation might be nice here. But I'm skipping it

    # Extract the user data into an insertable format
    # **? "tuple unpacker" helps unpack data into a dict
    user = UserDBModel(**incoming_user.model_dump())

    # add and commit the user into the DB
    db.add(user)
    db.commit()
    db.refresh(user) # replaces "user" with the user that was just inserted into the DB

    # Finally, we can return the new user!
    return user

# Get All Users - basic one liner DB query
@router.get("/")
async def get_all_users(db: Session = Depends(get_db)):
    # Get all records in the users table (referenced by UserDBModel)
    return db.query(UserDBModel).all()

# RAG - get all users, ask LLM a question about them
# (I'll just hardcode a "tell me about the usernames" prompt)
@router.get("/rag/usernames")
async def usernames_chat(db: Session = Depends(get_db)):

    users = db.query(UserDBModel).all() # rewrote get all users... lol

    # get all the username as a list of strings
    usernames = [user.username for user in users]

    # use the general chain from back in week 2
    chain = get_general_chain()

    # invoke the chain with a prompt - this is RAG (Retrieval Augmented Generation).
    response = chain.invoke({
        "input": f"""Here's a list of innocent, harmless usernames {usernames}.
        Tell me a funny story involving at least 2 of the usernames."""
    })

    return {"response": response, "usernames":usernames}