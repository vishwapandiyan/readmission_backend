"""
Authentication API Endpoints
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.user_models import (
    UserSignup, UserLogin, UserResponse, TokenResponse, PasswordChange
)
from app.services.auth_service import auth_service
from app.core.config import settings
from app.database import async_session_maker, UserDB
from sqlalchemy import select, func
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(signup_data: UserSignup):
    """
    Register a new user
    
    **Requirements:**
    - Username: 3-50 characters, alphanumeric and underscore only
    - Email: Valid email format
    - Password: At least 8 characters with uppercase, lowercase, and number
    - Passwords must match
    
    **Returns:**
    - Access token for immediate login
    - User information
    """
    try:
        logger.info(f"Signup attempt: {signup_data.username} ({signup_data.email})")
        
        # Create user
        user = await auth_service.create_user(signup_data)
        
        # Generate token
        access_token = auth_service.create_access_token(
            data={"sub": user.username, "user_id": user.id, "role": user.role},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        # Prepare response
        user_response = auth_service.user_to_response(user)
        
        logger.info(f"✓ User signed up: {user.username}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response
        )
    
    except ValueError as e:
        logger.warning(f"Signup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    """
    Authenticate user and get access token
    
    **Accepts:**
    - Username or email address
    - Password
    
    **Returns:**
    - Access token (expires in 30 minutes)
    - User information
    """
    try:
        logger.info(f"Login attempt: {login_data.username}")
        
        # Authenticate user
        user = await auth_service.authenticate_user(
            username=login_data.username,
            password=login_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Generate token
        access_token = auth_service.create_access_token(
            data={"sub": user.username, "user_id": user.id, "role": user.role},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        # Prepare response
        user_response = auth_service.user_to_response(user)
        
        logger.info(f"✓ User logged in: {user.username}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current authenticated user information
    
    **Requires:** Valid Bearer token in Authorization header
    """
    try:
        # Decode token
        token = credentials.credentials
        payload = auth_service.decode_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Get user
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        user = await auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        return auth_service.user_to_response(user)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChange,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Change user password
    
    **Requires:** 
    - Valid Bearer token
    - Current password
    - New password (meeting strength requirements)
    """
    try:
        # Decode token
        token = credentials.credentials
        payload = auth_service.decode_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        user_id = payload.get("user_id")
        
        # Update password
        success = await auth_service.update_password(
            user_id=user_id,
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        logger.info(f"✓ Password changed for user: {user_id}")
        
        return {
            "message": "Password changed successfully",
            "status": "success"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Logout user (client-side token removal)
    
    **Note:** JWT tokens are stateless. Actual logout happens client-side by removing the token.
    This endpoint is provided for logging purposes.
    """
    try:
        token = credentials.credentials
        payload = auth_service.decode_token(token)
        
        if payload:
            username = payload.get("sub")
            logger.info(f"User logged out: {username}")
        
        return {
            "message": "Logged out successfully",
            "status": "success"
        }
    
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return {
            "message": "Logged out",
            "status": "success"
        }


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Check authentication service health"""
    # Count users in database
    async with async_session_maker() as session:
        from sqlalchemy import func
        result = await session.execute(
            select(func.count(UserDB.id))
        )
        user_count = result.scalar()
    
    return {
        "status": "healthy",
        "service": "authentication",
        "users_count": user_count
    }
