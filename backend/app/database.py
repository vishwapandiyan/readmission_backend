"""
Database setup and session management for PostgreSQL
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON
from datetime import datetime
from app.core.config import settings, DATABASE_URL

# Create async engine with SSL for RDS
connect_args = {}
if settings.ENVIRONMENT == "production":
    # RDS requires SSL - asyncpg uses different syntax
    import ssl
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connect_args = {
        "ssl": ssl_context
    }

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args=connect_args
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()


# SQLAlchemy Models
class UserDB(Base):
    """User table"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(String(50), default="user", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)


class PatientDB(Base):
    """Patient table"""
    __tablename__ = "patients"
    
    patient_id = Column(String, primary_key=True, index=True)
    
    # Demographics
    age = Column(Integer, nullable=False)
    sex = Column(Integer, nullable=False)
    bmi = Column(Float, nullable=False)
    
    # Insurance & Admission
    insurance_type = Column(String(50), nullable=False)
    admission_type = Column(String(50), nullable=False)
    discharge_destination = Column(String(50), nullable=False)
    
    # Clinical Conditions
    comorbidity_index = Column(Integer, nullable=False)
    diabetes_flag = Column(Integer, nullable=False)
    heart_failure_flag = Column(Integer, nullable=False)
    copd_flag = Column(Integer, nullable=False)
    ckd_flag = Column(Integer, nullable=False)
    cancer_flag = Column(Integer, nullable=False)
    dementia_flag = Column(Integer, nullable=False)
    
    # Utilization History
    previous_admissions_12m = Column(Integer, nullable=False)
    previous_er_visits_12m = Column(Integer, nullable=False)
    prior_30_day_readmission_flag = Column(Integer, nullable=False)
    
    # Current Hospitalization
    length_of_stay_days = Column(Integer, nullable=False)
    icu_stay_flag = Column(Integer, nullable=False)
    
    # Medications
    medication_count_at_discharge = Column(Integer, nullable=False)
    polypharmacy_flag = Column(Integer, nullable=False)
    high_risk_medication_flag = Column(Integer, nullable=False)
    
    # Lab Values
    hemoglobin = Column(Float, nullable=False)
    creatinine = Column(Float, nullable=False)
    glucose = Column(Integer, nullable=False)
    hba1c = Column(Float, nullable=False)
    wbc_count = Column(Float, nullable=False)
    total_bilirubin = Column(Float, nullable=False)
    
    # Follow-up & Charges
    follow_up_within_7_days_flag = Column(Integer, nullable=False)
    total_charges_index_stay = Column(Float, nullable=False)
    
    # DRG Code
    drg_code = Column(String(20), nullable=True)
    
    # Optional metadata (not in CSV, added when creating patients manually)
    full_name = Column(String(200), nullable=True, default=None)
    contact_number = Column(String(20), nullable=True, default=None)
    emergency_contact = Column(String(200), nullable=True, default=None)
    notes = Column(Text, nullable=True, default=None)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    created_by = Column(String, nullable=True)
    
    # Prediction cache (stored as JSON)
    prediction_result = Column(JSON, nullable=True)
    intervention_result = Column(JSON, nullable=True)


class InterventionDB(Base):
    """Intervention tracking table"""
    __tablename__ = "interventions"
    
    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, nullable=False, index=True)
    risk_level = Column(String(20), nullable=False)
    risk_probability = Column(Float, nullable=False)
    
    # Intervention data (stored as JSON)
    immediate_actions = Column(JSON, nullable=False)
    follow_up_actions = Column(JSON, nullable=False)
    monitoring_plan = Column(JSON, nullable=False)
    
    # Optional personalized content
    personalized_care_plan = Column(Text, nullable=True)
    patient_education = Column(Text, nullable=True)
    care_coordinator_notes = Column(Text, nullable=True)
    
    # Timestamps
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String, nullable=True)


class AlertDB(Base):
    """Care team alerts table"""
    __tablename__ = "alerts"
    
    alert_id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, nullable=False, index=True)
    risk_level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False)
    assigned_to = Column(String(100), nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)


# Database dependency
async def get_db() -> AsyncSession:
    """Get database session"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Initialize database tables
async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Drop all tables (use with caution!)
async def drop_db():
    """Drop all database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
