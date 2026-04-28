"""Authentication routes."""

from fastapi import APIRouter, status

from app.deps import SessionDep
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.security import create_access_token
from app.services.auth_service import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, session: SessionDep) -> UserResponse:
    """Register a new user."""
    user = await register_user(session, payload.email, payload.password)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: SessionDep) -> TokenResponse:
    """Authenticate a user and return a bearer token."""
    user = await authenticate_user(session, payload.email, payload.password)
    return TokenResponse(access_token=create_access_token(user.id))
