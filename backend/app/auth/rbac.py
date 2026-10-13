from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.auth.jwt import decode_token
from app.models.user import User
from app.models.role import Role

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except HTTPException:
        raise
    except Exception:
        raise credentials_exception

    stmt = select(User).options(selectinload(User.role)).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if user is None:
        raise credentials_exception
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Enforces admin-only access at service/dependency level."""
    if not current_user.role or current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this action"
        )
    return current_user


async def require_staff_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """Allows staff or admin access."""
    if not current_user.role or current_user.role.name not in ("admin", "staff"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff or Admin privileges required"
        )
    return current_user
