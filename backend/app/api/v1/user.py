"""
User Endpoints
- Handles user registration and authentication
- Provides login functionality
- Returns JWT tokens for authenticated users
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.core.database import get_db
from app.api.models import User
from app.api.repositories.user import UserRepository
from app.api.schemas import TokenResponse, UserCreate, UserLogin
from app.api.v1.auth import authenticate_user, create_access_token

router = APIRouter()


@router.post(
    "/",
    tags=["User"],
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account and returns an access token",
)
async def create_user(user: UserCreate, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Create a new user account.

    Args:
        user: User registration details
        db: Database session

    Returns:
        TokenResponse: JWT access token

    Raises:
        HTTPException: If email is already registered
    """
    user_repo = UserRepository(db)

    if db.query(User).filter_by(user_email=user.user_email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    new_user, access_token = user_repo.create_user(user)
    return TokenResponse(access_token=access_token)


@router.post(
    "/auth/login",
    tags=["User"],
    response_model=TokenResponse,
    summary="Login user",
    description="Authenticate user and return access token",
)
async def login(user: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Authenticate user and generate access token.

    Args:
        user: Login credentials
        db: Database session

    Returns:
        TokenResponse: JWT access token

    Raises:
        HTTPException: If credentials are invalid
    """
    authenticated_user = authenticate_user(db, user.user_email, user.user_password)
    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user_id=str(authenticated_user.user_id))
    return TokenResponse(access_token=access_token)
