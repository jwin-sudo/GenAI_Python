# I want all user-based HTTP endpoints to be defined in this file.
from fastapi import APIRouter, HTTPException # type: ignore

from app.models.user_model import UserModel

# Set up this module as FastAPI router.
# We'll import this in main to make these endpoints accessible
router = APIRouter(
    prefix="/users", # HTTP requests ending in /users will be directed to this router
    tags=["users"] # This groups this routers endpoints under "users" in the /docs UI
)

# Temporary DB - just a python map of User models
user_database = {
    1: UserModel(
        id=1,
        username="Doofenshmirtz",
        password="password",
        email="platypush8r@gmail.com"
    ),
    2: UserModel(
        id=2,
        username="BigFrank",
        password="password",
        email="whofurted@aol.com"
    ),
    3: UserModel(
        id=3,
        username="JumbaGuy",
        password="password",
        email="jookiba@yahoo.com"
    )
}
# Create new users (POST request)
@router.post("/", status_code=201)
async def create_user(user: UserModel):

    # uniqueness validation for username (would be good to do this for email as well)
    for existing_user in user_database.values():
        if existing_user.username == user.username:
            raise HTTPException(status_code=400, detail="Username already exists!")

    # Give the user an auto-incremented ID 
    user.id = len(user_database) + 1

    # Store the user in the "DB"
    user_database[user.id] = user

    return {
        "message": user.username + " created successfully!",
        "inserted_user": user
    }
# Get all users (GET request)
@router.get("/")
async def get_all_users():
    return user_database

# Delete a specific user by ID (DELETE request + path variable)
# notice how we include {path variables} in the route. the route is now /users/{some user_id}
@router.delete("/{user_id}")
async def delete_user(user_id: int):

    # if the passed in user id exists as a key in the map, pop that User out 
    if user_id in user_database:
        deleted_user = user_database.pop(user_id)
        return {
            "message": f"User {deleted_user.username} deleted successfully!", 
            "deleted_user": deleted_user
        }
    else:
        raise HTTPException(status_code=404, detail="User ID not found - can't delete!")

# Update a specific user's info by ID (PUT request + path variable)
@router.put("/{user_id}")
async def update_user(user_id: int, updated_user: UserModel):
    #Similarly to the delete above, check if the User ID exists 
    if user_id in user_database:
        # update all the user fields EXCEPT the ID
        user_database[user_id].username = updated_user.username
        user_database[user_id].password = updated_user.password
        user_database[user_id].email = updated_user.email
        return {
            "message": f"{user_database[user_id].username} updated successfully!",
            "updated_user": user_database[user_id]
        }
    
    else:
        raise HTTPException(status_code=404, detail="User ID not found - can't update!")
