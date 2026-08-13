"""
Care Coordinator and Care Plan Service
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid
import random

from app.models.care_models import (
    CarePlan,
    CarePlanCreate,
    CarePlanUpdate,
    CarePlanResponse,
    CareStatus,
    DEFAULT_COORDINATORS,
)


class CareService:
    """Service for managing care plans and coordinators"""
    
    def __init__(self):
        # In-memory storage (replace with database in production)
        self.care_plans: Dict[str, CarePlan] = {}
        self.coordinators = {c.id: c for c in DEFAULT_COORDINATORS}
    
    def create_care_plan(self, data: CarePlanCreate) -> CarePlan:
        """Create a new care plan"""
        care_plan_id = f"CP-{uuid.uuid4().hex[:8].upper()}"
        
        # Auto-assign coordinator if not provided
        coordinator_id = data.coordinator_id
        if not coordinator_id:
            coordinator_id = random.choice(list(self.coordinators.keys()))
        
        coordinator = self.coordinators.get(coordinator_id)
        
        # Default follow-up date to 7 days if not provided
        follow_up_date = data.follow_up_date or datetime.now() + timedelta(days=7)
        
        care_plan = CarePlan(
            care_plan_id=care_plan_id,
            patient_id=data.patient_id,
            coordinator_id=coordinator_id,
            coordinator_name=coordinator.name if coordinator else None,
            follow_up_date=follow_up_date,
            notes=data.notes,
        )
        
        self.care_plans[care_plan_id] = care_plan
        return care_plan
    
    def get_care_plan(self, care_plan_id: str) -> Optional[CarePlan]:
        """Get care plan by ID"""
        return self.care_plans.get(care_plan_id)
    
    def get_care_plan_by_patient(self, patient_id: str) -> Optional[CarePlan]:
        """Get care plan for a patient"""
        for plan in self.care_plans.values():
            if plan.patient_id == patient_id:
                return plan
        return None
    
    def list_care_plans(
        self,
        status: Optional[CareStatus] = None,
        coordinator_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CarePlan]:
        """List care plans with filters"""
        plans = list(self.care_plans.values())
        
        # Apply filters
        if status:
            plans = [p for p in plans if p.status == status]
        if coordinator_id:
            plans = [p for p in plans if p.coordinator_id == coordinator_id]
        
        # Pagination
        return plans[skip : skip + limit]
    
    def update_care_plan(
        self, care_plan_id: str, update_data: CarePlanUpdate
    ) -> Optional[CarePlan]:
        """Update care plan"""
        plan = self.care_plans.get(care_plan_id)
        if not plan:
            return None
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(plan, key, value)
        
        # Update coordinator name if coordinator_id changed
        if update_data.coordinator_id:
            coordinator = self.coordinators.get(update_data.coordinator_id)
            if coordinator:
                plan.coordinator_name = coordinator.name
        
        plan.updated_at = datetime.now()
        
        # Auto-complete if all tasks done
        if self._all_tasks_completed(plan):
            plan.status = CareStatus.COMPLETED
            plan.completed_at = datetime.now()
        
        return plan
    
    def delete_care_plan(self, care_plan_id: str) -> bool:
        """Delete care plan"""
        if care_plan_id in self.care_plans:
            del self.care_plans[care_plan_id]
            return True
        return False
    
    def get_coordinators(self) -> List[dict]:
        """Get all care coordinators"""
        return [c.model_dump() for c in self.coordinators.values()]
    
    def care_plan_to_response(self, plan: CarePlan) -> CarePlanResponse:
        """Convert care plan to response format"""
        progress = self._calculate_progress(plan)
        
        return CarePlanResponse(
            care_plan_id=plan.care_plan_id,
            patient_id=plan.patient_id,
            status=plan.status,
            coordinator_id=plan.coordinator_id,
            coordinator_name=plan.coordinator_name,
            follow_up_date=plan.follow_up_date,
            progress_percentage=progress,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )
    
    def _calculate_progress(self, plan: CarePlan) -> int:
        """Calculate completion percentage"""
        tasks = [
            plan.medication_reconciliation,
            plan.follow_up_appointment,
            plan.patient_education,
            plan.follow_up_call,
            plan.home_health_assessment,
            plan.primary_care_coordination,
            plan.specialist_referral,
        ]
        
        completed = sum(1 for t in tasks if t)
        total = len(tasks)
        
        return int((completed / total) * 100) if total > 0 else 0
    
    def _all_tasks_completed(self, plan: CarePlan) -> bool:
        """Check if all required tasks are completed"""
        return all([
            plan.medication_reconciliation,
            plan.follow_up_appointment,
            plan.patient_education,
            plan.follow_up_call,
            plan.home_health_assessment,
            plan.primary_care_coordination,
        ])
    
    def get_care_stats(self) -> dict:
        """Get care statistics"""
        plans = list(self.care_plans.values())
        
        total = len(plans)
        pending = sum(1 for p in plans if p.status == CareStatus.PENDING)
        in_progress = sum(1 for p in plans if p.status == CareStatus.IN_PROGRESS)
        completed = sum(1 for p in plans if p.status == CareStatus.COMPLETED)
        overdue = sum(1 for p in plans if p.status == CareStatus.OVERDUE)
        
        # Calculate due today
        today = datetime.now().date()
        due_today = sum(
            1 for p in plans
            if p.follow_up_date and p.follow_up_date.date() == today
        )
        
        return {
            "total_care_plans": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "overdue": overdue,
            "calls_due_today": due_today,
            "completion_rate": round((completed / total * 100) if total > 0 else 0, 1),
        }


# Singleton instance
care_service = CareService()
