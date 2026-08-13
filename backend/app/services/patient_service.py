"""
Patient Management Service
Handles patient CRUD operations and automatic prediction triggering
"""
from app.models.patient_models import Patient, PatientCreate, PatientUpdate, PatientResponse
from app.models.schemas import PatientFeatures
from app.models.intervention_models import InterventionRequest, RiskFactors
from app.services.prediction_service import prediction_service
from app.services.intervention_service import intervention_service
from app.database import async_session_maker, PatientDB
from sqlalchemy import select
from typing import Dict, List, Optional
from datetime import datetime
import uuid
import logging
import asyncio

logger = logging.getLogger(__name__)


class PatientService:
    """Service for patient management operations"""
    
    @classmethod
    def generate_patient_id(cls) -> str:
        """Generate unique patient ID"""
        return f"P{str(uuid.uuid4().hex[:6]).upper()}"
    
    @classmethod
    async def create_patient_async(cls, patient_data: PatientCreate, created_by: Optional[str] = None) -> dict:
        """
        Create new patient and optionally trigger prediction (async version)
        
        Returns:
        - patient: Patient information
        - prediction: Readmission prediction (if auto_predict=True)
        - interventions: Care interventions (if auto_generate_interventions=True)
        """
        logger.info(f"Creating new patient...")
        
        # Generate patient ID if not provided
        patient_id = patient_data.patient_id or cls.generate_patient_id()
        
        async with async_session_maker() as session:
            # Check if patient ID already exists
            result = await session.execute(
                select(PatientDB).where(PatientDB.patient_id == patient_id)
            )
            if result.scalar_one_or_none():
                raise ValueError(f"Patient ID {patient_id} already exists")
            
            # Create patient database object
            patient_db = PatientDB(
                patient_id=patient_id,
                age=patient_data.age,
                sex=patient_data.sex,
                bmi=patient_data.bmi,
                insurance_type=patient_data.insurance_type.value,
                admission_type=patient_data.admission_type.value,
                discharge_destination=patient_data.discharge_destination.value,
                comorbidity_index=patient_data.comorbidity_index,
                diabetes_flag=patient_data.diabetes_flag,
                heart_failure_flag=patient_data.heart_failure_flag,
                copd_flag=patient_data.copd_flag,
                ckd_flag=patient_data.ckd_flag,
                cancer_flag=patient_data.cancer_flag,
                dementia_flag=patient_data.dementia_flag,
                previous_admissions_12m=patient_data.previous_admissions_12m,
                previous_er_visits_12m=patient_data.previous_er_visits_12m,
                prior_30_day_readmission_flag=patient_data.prior_30_day_readmission_flag,
                length_of_stay_days=patient_data.length_of_stay_days,
                icu_stay_flag=patient_data.icu_stay_flag,
                medication_count_at_discharge=patient_data.medication_count_at_discharge,
                polypharmacy_flag=patient_data.polypharmacy_flag,
                high_risk_medication_flag=patient_data.high_risk_medication_flag,
                hemoglobin=patient_data.hemoglobin,
                creatinine=patient_data.creatinine,
                glucose=patient_data.glucose,
                hba1c=patient_data.hba1c,
                wbc_count=patient_data.wbc_count,
                total_bilirubin=patient_data.total_bilirubin,
                follow_up_within_7_days_flag=patient_data.follow_up_within_7_days_flag,
                total_charges_index_stay=patient_data.total_charges_index_stay,
                drg_code=patient_data.drg_code,
                full_name=patient_data.full_name,
                contact_number=patient_data.contact_number,
                emergency_contact=patient_data.emergency_contact,
                notes=patient_data.notes,
                created_at=datetime.utcnow(),
                created_by=created_by
            )
            
            session.add(patient_db)
            await session.commit()
            await session.refresh(patient_db)
            
            logger.info(f"✓ Patient created: {patient_id}")
            
            patient = cls.db_to_model(patient_db)
            
            result = {
                "patient": cls.patient_to_response(patient),
                "prediction": None,
                "interventions": None
            }
            
            # Auto-trigger prediction if requested
            if patient_data.auto_predict:
                logger.info(f"Auto-triggering prediction for patient {patient_id}...")
                try:
                    prediction_result = await cls.predict_readmission_async(patient_id)
                    result["prediction"] = prediction_result
                    logger.info(f"✓ Prediction completed: {prediction_result['readmission_probability']:.1%} risk")
                    
                    # Auto-generate interventions if requested
                    if patient_data.auto_generate_interventions and prediction_result:
                        logger.info(f"Auto-generating interventions for patient {patient_id}...")
                        try:
                            intervention_result = await cls.generate_interventions_async(
                                patient_id=patient_id,
                                use_llm=patient_data.use_llm_personalization
                            )
                            result["interventions"] = intervention_result
                            logger.info(f"✓ Interventions generated: {intervention_result['risk_level']} risk")
                        except Exception as e:
                            logger.error(f"Intervention generation failed: {e}")
                
                except Exception as e:
                    logger.error(f"Prediction failed: {e}")
            
            return result
    
    @classmethod
    def create_patient(cls, patient_data: PatientCreate, created_by: Optional[str] = None) -> dict:
        """Sync wrapper for create_patient_async"""
        return asyncio.run(cls.create_patient_async(patient_data, created_by))
    
    @classmethod
    async def get_patient_async(cls, patient_id: str) -> Optional[Patient]:
        """Get patient by ID (async version)"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(PatientDB).where(PatientDB.patient_id == patient_id)
            )
            patient_db = result.scalar_one_or_none()
            return cls.db_to_model(patient_db) if patient_db else None
    
    @classmethod
    def get_patient(cls, patient_id: str) -> Optional[Patient]:
        """Sync wrapper for get_patient_async"""
        return asyncio.run(cls.get_patient_async(patient_id))
    
    @classmethod
    async def list_patients_async(cls, skip: int = 0, limit: int = 100) -> List[Patient]:
        """List all patients with pagination (async version)"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(PatientDB).offset(skip).limit(limit)
            )
            patients_db = result.scalars().all()
            return [cls.db_to_model(p) for p in patients_db]
    
    @classmethod
    def list_patients(cls, skip: int = 0, limit: int = 100) -> List[Patient]:
        """Sync wrapper for list_patients_async"""
        return asyncio.run(cls.list_patients_async(skip, limit))
    
    @classmethod
    async def update_patient_async(cls, patient_id: str, update_data: PatientUpdate) -> Optional[Patient]:
        """Update patient information (async version)"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(PatientDB).where(PatientDB.patient_id == patient_id)
            )
            patient_db = result.scalar_one_or_none()
            
            if not patient_db:
                return None
            
            # Update only provided fields
            update_dict = update_data.model_dump(exclude_unset=True)
            for field, value in update_dict.items():
                if hasattr(patient_db, field):
                    setattr(patient_db, field, value)
            
            patient_db.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(patient_db)
            
            logger.info(f"✓ Patient updated: {patient_id}")
            return cls.db_to_model(patient_db)
    
    @classmethod
    def update_patient(cls, patient_id: str, update_data: PatientUpdate) -> Optional[Patient]:
        """Sync wrapper for update_patient_async"""
        return asyncio.run(cls.update_patient_async(patient_id, update_data))
    
    @classmethod
    async def delete_patient_async(cls, patient_id: str) -> bool:
        """Delete patient (async version)"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(PatientDB).where(PatientDB.patient_id == patient_id)
            )
            patient_db = result.scalar_one_or_none()
            
            if patient_db:
                await session.delete(patient_db)
                await session.commit()
                logger.info(f"✓ Patient deleted: {patient_id}")
                return True
            return False
    
    @classmethod
    def delete_patient(cls, patient_id: str) -> bool:
        """Sync wrapper for delete_patient_async"""
        return asyncio.run(cls.delete_patient_async(patient_id))
    
    @classmethod
    def _ensure_required_fields(cls, patient) -> dict:
        """
        Ensure all required fields have values, filling in safe defaults for missing fields.
        This prevents prediction errors when optional fields are None.
        
        IMPORTANT: Field names must match training data exactly:
        - Use 'hba1c' NOT 'hbA1c'
        - Include 'drg_code' field
        """
        return {
            'age': patient.age,
            'sex': patient.sex,
            'bmi': patient.bmi or 28.0,  # Default to normal BMI
            'insurance_type': patient.insurance_type,
            'admission_type': patient.admission_type,
            'discharge_destination': patient.discharge_destination,
            'comorbidity_index': patient.comorbidity_index or 0,
            'diabetes_flag': patient.diabetes_flag or 0,
            'heart_failure_flag': patient.heart_failure_flag or 0,
            'copd_flag': patient.copd_flag or 0,
            'ckd_flag': patient.ckd_flag or 0,
            'cancer_flag': patient.cancer_flag or 0,
            'dementia_flag': patient.dementia_flag or 0,
            'previous_admissions_12m': patient.previous_admissions_12m or 0,
            'previous_er_visits_12m': patient.previous_er_visits_12m or 0,
            'prior_30_day_readmission_flag': patient.prior_30_day_readmission_flag or 0,
            'length_of_stay_days': patient.length_of_stay_days or 3,
            'icu_stay_flag': patient.icu_stay_flag or 0,
            'medication_count_at_discharge': patient.medication_count_at_discharge or 5,
            'polypharmacy_flag': patient.polypharmacy_flag or 0,
            'high_risk_medication_flag': patient.high_risk_medication_flag or 0,
            'hemoglobin': patient.hemoglobin or 13.5,  # Normal hemoglobin
            'creatinine': patient.creatinine or 1.0,   # Normal creatinine
            'glucose': float(patient.glucose or 100),   # Normal glucose
            'hba1c': patient.hba1c or 6.0,             # ✅ FIXED: lowercase to match training
            'wbc_count': patient.wbc_count or 7.5,     # Normal WBC
            'total_bilirubin': patient.total_bilirubin or 0.8,  # Normal bilirubin
            'follow_up_within_7_days_flag': patient.follow_up_within_7_days_flag or 0,
            'total_charges_index_stay': patient.total_charges_index_stay or 10000,
            'drg_code': patient.drg_code or '291',      # ✅ ADDED: drg_code field
        }
    
    @classmethod
    async def predict_readmission_async(cls, patient_id: str) -> dict:
        """Run readmission prediction for patient (async version)"""
        patient = await cls.get_patient_async(patient_id)
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")
        
        # Get patient data with defaults for missing fields
        patient_data = cls._ensure_required_fields(patient)
        
        # Prepare prediction request
        prediction_request = PatientFeatures(**patient_data)
        
        # Get prediction
        prediction = prediction_service.predict(prediction_request)
        
        # Convert to dict with mode='json' to handle datetime serialization
        prediction_dict = prediction.model_dump(mode='json')
        
        # Add backward compatibility fields at root level for the endpoint
        prediction_dict['readmission_probability'] = prediction.layer1_prediction.probability
        prediction_dict['risk_level'] = prediction.layer2_risk_level.risk_tier
        prediction_dict['will_readmit'] = prediction.layer1_prediction.will_readmit
        
        # Cache result in database
        async with async_session_maker() as session:
            result = await session.execute(
                select(PatientDB).where(PatientDB.patient_id == patient_id)
            )
            patient_db = result.scalar_one_or_none()
            if patient_db:
                patient_db.prediction_result = prediction_dict
                await session.commit()
        
        return prediction_dict
    
    @classmethod
    def predict_readmission(cls, patient_id: str) -> dict:
        """Sync wrapper for predict_readmission_async"""
        return asyncio.run(cls.predict_readmission_async(patient_id))
    
    @classmethod
    async def generate_interventions_async(cls, patient_id: str, use_llm: bool = False) -> dict:
        """Generate care interventions for patient (async version)"""
        patient = await cls.get_patient_async(patient_id)
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")
        
        # Get prediction if not already available
        if not patient.prediction_result:
            await cls.predict_readmission_async(patient_id)
            patient = await cls.get_patient_async(patient_id)
        
        # Build condition list
        conditions = []
        if patient.diabetes_flag:
            conditions.append("diabetes")
        if patient.heart_failure_flag:
            conditions.append("heart_failure")
        if patient.copd_flag:
            conditions.append("copd")
        if patient.ckd_flag:
            conditions.append("ckd")
        if patient.cancer_flag:
            conditions.append("cancer")
        if patient.dementia_flag:
            conditions.append("dementia")
        
        # Prepare intervention request
        intervention_request = InterventionRequest(
            patient_id=patient_id,
            risk_probability=patient.prediction_result["readmission_probability"],
            risk_factors=RiskFactors(
                comorbidity_index=patient.comorbidity_index,
                previous_admissions_12m=patient.previous_admissions_12m,
                conditions=conditions,
                medications_count=patient.medication_count_at_discharge,
                age=patient.age,
                icu_stay=bool(patient.icu_stay_flag),
                discharge_destination=patient.discharge_destination
            ),
            use_llm_personalization=use_llm
        )
        
        # Generate interventions
        interventions = intervention_service.generate_interventions(intervention_request)
        
        # Convert to dict with mode='json' to handle datetime serialization
        interventions_dict = interventions.model_dump(mode='json')
        
        # Cache result in database
        async with async_session_maker() as session:
            result = await session.execute(
                select(PatientDB).where(PatientDB.patient_id == patient_id)
            )
            patient_db = result.scalar_one_or_none()
            if patient_db:
                patient_db.intervention_result = interventions_dict
                await session.commit()
        
        return interventions_dict
    
    @classmethod
    def generate_interventions(cls, patient_id: str, use_llm: bool = False) -> dict:
        """Sync wrapper for generate_interventions_async"""
        return asyncio.run(cls.generate_interventions_async(patient_id, use_llm))
    
    @staticmethod
    def db_to_model(patient_db: PatientDB) -> Patient:
        """Convert PatientDB to Patient model"""
        return Patient(
            patient_id=patient_db.patient_id,
            age=patient_db.age,
            sex=patient_db.sex,
            bmi=patient_db.bmi,
            insurance_type=patient_db.insurance_type,
            admission_type=patient_db.admission_type,
            discharge_destination=patient_db.discharge_destination,
            comorbidity_index=patient_db.comorbidity_index,
            diabetes_flag=patient_db.diabetes_flag,
            heart_failure_flag=patient_db.heart_failure_flag,
            copd_flag=patient_db.copd_flag,
            ckd_flag=patient_db.ckd_flag,
            cancer_flag=patient_db.cancer_flag,
            dementia_flag=patient_db.dementia_flag,
            previous_admissions_12m=patient_db.previous_admissions_12m,
            previous_er_visits_12m=patient_db.previous_er_visits_12m,
            prior_30_day_readmission_flag=patient_db.prior_30_day_readmission_flag,
            length_of_stay_days=patient_db.length_of_stay_days,
            icu_stay_flag=patient_db.icu_stay_flag,
            medication_count_at_discharge=patient_db.medication_count_at_discharge,
            polypharmacy_flag=patient_db.polypharmacy_flag,
            high_risk_medication_flag=patient_db.high_risk_medication_flag,
            hemoglobin=patient_db.hemoglobin,
            creatinine=patient_db.creatinine,
            glucose=patient_db.glucose,
            hba1c=patient_db.hba1c,
            wbc_count=patient_db.wbc_count,
            total_bilirubin=patient_db.total_bilirubin,
            follow_up_within_7_days_flag=patient_db.follow_up_within_7_days_flag,
            total_charges_index_stay=patient_db.total_charges_index_stay,
            drg_code=patient_db.drg_code,
            full_name=patient_db.full_name,
            contact_number=patient_db.contact_number,
            emergency_contact=patient_db.emergency_contact,
            notes=patient_db.notes,
            created_at=patient_db.created_at,
            updated_at=patient_db.updated_at,
            created_by=patient_db.created_by,
            prediction_result=patient_db.prediction_result,
            intervention_result=patient_db.intervention_result
        )
    
    @staticmethod
    def patient_to_response(patient: Patient) -> PatientResponse:
        """Convert Patient to PatientResponse - COMPLETE with all fields"""
        return PatientResponse(
            patient_id=patient.patient_id,
            age=patient.age,
            sex=patient.sex,
            bmi=patient.bmi,
            insurance_type=patient.insurance_type,
            admission_type=patient.admission_type,
            discharge_destination=patient.discharge_destination,
            comorbidity_index=patient.comorbidity_index,
            full_name=patient.full_name,
            created_at=patient.created_at,
            updated_at=patient.updated_at,
            created_by=patient.created_by,
            has_prediction=patient.prediction_result is not None,
            readmission_probability=patient.prediction_result.get("readmission_probability") if patient.prediction_result else None,
            risk_level=patient.intervention_result.get("risk_level") if patient.intervention_result else None,
            # ALL clinical fields (fixed undefined display issue)
            diabetes_flag=patient.diabetes_flag,
            heart_failure_flag=patient.heart_failure_flag,
            copd_flag=patient.copd_flag,
            ckd_flag=patient.ckd_flag,
            cancer_flag=patient.cancer_flag,
            dementia_flag=patient.dementia_flag,
            previous_admissions_12m=patient.previous_admissions_12m,
            previous_er_visits_12m=patient.previous_er_visits_12m,
            prior_30_day_readmission_flag=patient.prior_30_day_readmission_flag,
            length_of_stay_days=patient.length_of_stay_days,
            icu_stay_flag=patient.icu_stay_flag,
            medication_count_at_discharge=patient.medication_count_at_discharge,
            polypharmacy_flag=patient.polypharmacy_flag,
            high_risk_medication_flag=patient.high_risk_medication_flag,
            hemoglobin=patient.hemoglobin,
            creatinine=patient.creatinine,
            glucose=patient.glucose,
            hba1c=patient.hba1c,
            wbc_count=patient.wbc_count,
            total_bilirubin=patient.total_bilirubin,
            follow_up_within_7_days_flag=patient.follow_up_within_7_days_flag,
            total_charges_index_stay=patient.total_charges_index_stay,
            drg_code=patient.drg_code,
            contact_number=patient.contact_number,
            emergency_contact=patient.emergency_contact,
            notes=patient.notes
        )


# Singleton instance
patient_service = PatientService()
