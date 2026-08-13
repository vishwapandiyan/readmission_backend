"""
Authentication Service
Handles user registration, login, password hashing, and JWT tokens
"""
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from app.core.config import settings
from app.models.user_models import User, UserSignup, UserResponse
from app.database import async_session_maker, UserDB
from sqlalchemy import select
import uuid
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt (automatically handles 72-byte limit)"""
        # Bcrypt automatically truncates to 72 bytes, but we'll do it explicitly for clarity
        password_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a bcrypt hash"""
        # Bcrypt automatically handles the 72-byte limit
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError as e:
            logger.error(f"JWT decode error: {e}")
            return None
    
    @classmethod
    async def get_user_by_username(cls, username: str) -> Optional[User]:
        """Get user by username"""
        username = username.lower()
        async with async_session_maker() as session:
            result = await session.execute(
                select(UserDB).where(UserDB.username == username)
            )
            user_db = result.scalar_one_or_none()
            return cls.db_to_model(user_db) if user_db else None
    
    @classmethod
    async def get_user_by_email(cls, email: str) -> Optional[User]:
        """Get user by email"""
        email = email.lower()
        async with async_session_maker() as session:
            result = await session.execute(
                select(UserDB).where(UserDB.email == email)
            )
            user_db = result.scalar_one_or_none()
            return cls.db_to_model(user_db) if user_db else None
    
    @classmethod
    async def get_user_by_id(cls, user_id: str) -> Optional[User]:
        """Get user by ID"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(UserDB).where(UserDB.id == user_id)
            )
            user_db = result.scalar_one_or_none()
            return cls.db_to_model(user_db) if user_db else None
    
    @classmethod
    async def create_user(cls, signup_data: UserSignup) -> User:
        """Create a new user in database"""
        # Check if username exists
        existing_user = await cls.get_user_by_username(signup_data.username)
        if existing_user:
            raise ValueError(f"Username '{signup_data.username}' already exists")
        
        # Check if email exists
        existing_email = await cls.get_user_by_email(signup_data.email)
        if existing_email:
            raise ValueError(f"Email '{signup_data.email}' already registered")
        
        # Create user
        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        hashed_password = cls.hash_password(signup_data.password)
        
        user_db = UserDB(
            id=user_id,
            username=signup_data.username.lower(),
            email=signup_data.email.lower(),
            hashed_password=hashed_password,
            full_name=signup_data.full_name,
            role=signup_data.role or "user",
            is_active=True,
            is_superuser=False,
            created_at=datetime.utcnow()
        )
        
        # Save to database
        async with async_session_maker() as session:
            session.add(user_db)
            await session.commit()
            await session.refresh(user_db)
        
        logger.info(f"✓ User created in database: {user_db.username} ({user_db.email})")
        return cls.db_to_model(user_db)
    
    @classmethod
    async def authenticate_user(cls, username: str, password: str) -> Optional[User]:
        """Authenticate user with username/email and password"""
        # Try username first
        user = await cls.get_user_by_username(username)
        
        # Try email if username not found
        if not user and '@' in username:
            user = await cls.get_user_by_email(username)
        
        if not user:
            logger.warning(f"Login attempt with non-existent user: {username}")
            return None
        
        if not user.is_active:
            logger.warning(f"Login attempt with inactive user: {username}")
            return None
        
        if not cls.verify_password(password, user.hashed_password):
            logger.warning(f"Failed login attempt for user: {username}")
            return None
        
        # Update last login
        async with async_session_maker() as session:
            result = await session.execute(
                select(UserDB).where(UserDB.id == user.id)
            )
            user_db = result.scalar_one_or_none()
            if user_db:
                user_db.last_login = datetime.utcnow()
                await session.commit()
        
        logger.info(f"✓ User authenticated: {user.username}")
        return user
    
    @classmethod
    async def update_password(cls, user_id: str, current_password: str, new_password: str) -> bool:
        """Update user password"""
        user = await cls.get_user_by_id(user_id)
        if not user:
            return False
        
        # Verify current password
        if not cls.verify_password(current_password, user.hashed_password):
            return False
        
        # Update password in database
        async with async_session_maker() as session:
            result = await session.execute(
                select(UserDB).where(UserDB.id == user_id)
            )
            user_db = result.scalar_one_or_none()
            if user_db:
                user_db.hashed_password = cls.hash_password(new_password)
                user_db.updated_at = datetime.utcnow()
                await session.commit()
        
        logger.info(f"✓ Password updated for user: {user.username}")
        return True
    
    @staticmethod
    def db_to_model(user_db: UserDB) -> User:
        """Convert UserDB to User model"""
        return User(
            id=user_db.id,
            username=user_db.username,
            email=user_db.email,
            hashed_password=user_db.hashed_password,
            full_name=user_db.full_name,
            role=user_db.role,
            is_active=user_db.is_active,
            is_superuser=user_db.is_superuser,
            created_at=user_db.created_at,
            updated_at=user_db.updated_at,
            last_login=user_db.last_login
        )
    
    @staticmethod
    def user_to_response(user: User) -> UserResponse:
        """Convert User to UserResponse"""
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at
        )


# Create singleton instance
auth_service = AuthService()


# Create default admin user for testing
async def create_default_users():
    """Create default users for testing"""
    try:
        # Admin user - using simple password within 72 bytes
        admin_signup = UserSignup(
            username="admin",
            email="admin@hospital.com",
            password="Admin123",
            confirm_password="Admin123",
            full_name="System Administrator",
            role="admin"
        )
        admin = await auth_service.create_user(admin_signup)
        
        # Make admin superuser
        async with async_session_maker() as session:
            result = await session.execute(
                select(UserDB).where(UserDB.id == admin.id)
            )
            user_db = result.scalar_one_or_none()
            if user_db:
                user_db.is_superuser = True
                await session.commit()
        
        logger.info("✓ Default admin user created")
        
        # Test physician
        physician_signup = UserSignup(
            username="dr_smith",
            email="dr.smith@hospital.com",
            password="Doctor123",
            confirm_password="Doctor123",
            full_name="Dr. Sarah Smith",
            role="physician"
        )
        await auth_service.create_user(physician_signup)
        logger.info("✓ Default physician user created")
        
        # Test nurse
        nurse_signup = UserSignup(
            username="nurse_jane",
            email="jane.nurse@hospital.com",
            password="Nurse123",
            confirm_password="Nurse123",
            full_name="Jane Nurse",
            role="nurse"
        )
        await auth_service.create_user(nurse_signup)
        logger.info("✓ Default nurse user created")
        
    except ValueError as e:
        logger.info(f"Default users already exist: {e}")
    except Exception as e:
        logger.error(f"Error creating default users: {e}")
