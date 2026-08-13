"""
User Authentication Models
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime


class UserSignup(BaseModel):
    """User registration request"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, max_length=200, description="Password")
    confirm_password: str = Field(..., description="Password confirmation")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    role: Optional[str] = Field(default="user", description="User role")
    
    @validator('username')
    def username_alphanumeric(cls, v):
        """Validate username contains only alphanumeric and underscore"""
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v.lower()
    
    @validator('password')
    def password_strength(cls, v):
        """Validate password strength and truncate to 72 bytes for bcrypt"""
        # Truncate to 72 bytes for bcrypt compatibility
        password_bytes = v.encode('utf-8')[:72]
        truncated = password_bytes.decode('utf-8', errors='ignore')
        
        if len(truncated) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in truncated):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in truncated):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in truncated):
            raise ValueError('Password must contain at least one number')
        return truncated
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Validate passwords match (after password has been truncated)"""
        if 'password' in values:
            # Truncate confirm_password the same way
            password_bytes = v.encode('utf-8')[:72]
            truncated = password_bytes.decode('utf-8', errors='ignore')
            if truncated != values['password']:
                raise ValueError('Passwords do not match')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john.doe@hospital.com",
                "password": "SecurePass123",
                "confirm_password": "SecurePass123",
                "full_name": "Dr. John Doe",
                "role": "physician"
            }
        }


class UserLogin(BaseModel):
    """User login request"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "password": "SecurePass123"
            }
        }


class UserResponse(BaseModel):
    """User information response"""
    id: str
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "usr_123456",
                "username": "john_doe",
                "email": "john.doe@hospital.com",
                "full_name": "Dr. John Doe",
                "role": "physician",
                "is_active": True,
                "created_at": "2026-08-11T10:00:00Z"
            }
        }


class TokenResponse(BaseModel):
    """Authentication token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes
    user: UserResponse
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": "usr_123456",
                    "username": "john_doe",
                    "email": "john.doe@hospital.com",
                    "full_name": "Dr. John Doe",
                    "role": "physician",
                    "is_active": True,
                    "created_at": "2026-08-11T10:00:00Z"
                }
            }
        }


class PasswordChange(BaseModel):
    """Password change request"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_new_password: str = Field(..., description="Confirm new password")
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class User(BaseModel):
    """Internal user model (for database)"""
    id: str
    username: str
    email: str
    hashed_password: str
    full_name: Optional[str] = None
    role: str = "user"
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
