from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.auth import UserLogin, Token, TokenRefreshRequest, UserResponse
from app.repositories.user_repo import UserRepository
from app.auth.password import verify_password
from app.auth.jwt import create_access_token, create_refresh_token, decode_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    user = await user_repo.get_by_username(credentials.username)

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role_name = user.role.name if user.role else "staff"

    access_token = create_access_token(
        data={"sub": user.id, "username": user.username, "role": role_name}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.id}
    )

    user_resp = UserResponse(
        id=user.id,
        username=user.username,
        role=role_name,
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user_resp,
    )


@router.post("/refresh")
async def refresh_token(request: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(request.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    role_name = user.role.name if user.role else "staff"
    new_access_token = create_access_token(
        data={"sub": user.id, "username": user.username, "role": role_name}
    )
    return {"access_token": new_access_token, "token_type": "bearer"}
