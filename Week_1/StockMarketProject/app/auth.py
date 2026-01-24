from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext

SECRET_KEY = "change-this-to-a-secure-random-string"  # put in env for real apps
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# use argon2 to avoid bcrypt 72-byte limitation
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
router = APIRouter()

# regenerate demo users with the new context
fake_users_db = {
    "alice": {"username": "alice", "hashed_password": pwd_context.hash("secret1")},
    "bob": {"username": "bob", "hashed_password": pwd_context.hash("secret2")},
}

token_blacklist = set()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if plain_password is None:
        return False
    # defensive check: don't accidentally verify extremely long strings (helps catch bugs)
    if isinstance(plain_password, str) and len(plain_password.encode("utf-8")) > 1024:
        # treat this as a client error rather than blowing up inside bcrypt
        raise HTTPException(status_code=400, detail="Password length is invalid")
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return {"username": username}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token({"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    token_blacklist.add(token)
    return {"message": "Logged out"}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    if token in token_blacklist:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise JWTError()
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = fake_users_db.get(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return {"username": username}