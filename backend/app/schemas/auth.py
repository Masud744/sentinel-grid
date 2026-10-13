from typing import Optional
from pydantic import BaseModel


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    user_id: str
    username: str
    role: str
