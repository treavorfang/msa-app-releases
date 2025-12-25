from fastapi import APIRouter
from typing import List, Dict, Any
from datetime import date
from services.technician_service import TechnicianService
from services.technician_performance_service import TechnicianPerformanceService
from services.audit_service import AuditService

router = APIRouter()
audit_service = AuditService()
tech_service = TechnicianService(audit_service)
perf_service = TechnicianPerformanceService()

@router.get("/")
async def get_technicians():
    """List all active technicians."""
    techs = tech_service.get_active_technicians()
    
    return [{
        "id": t.id,
        "name": t.full_name
    } for t in techs]

@router.get("/{technician_id}/performance")
async def get_technician_performance(technician_id: int):
    """Get performance stats for a technician."""
    summary = perf_service.get_year_to_date_summary(technician_id)
    
    # Convert Decimals in summary to float for JSON
    clean_summary = {}
    for k, v in summary.items():
        if hasattr(v, 'quantize'):  # Is Decimal check
            clean_summary[k] = float(v)
        else:
            clean_summary[k] = v
            
    current_month_perf = perf_service.get_performance(technician_id, date.today())
    
    return {
        "summary": clean_summary,
        "current_month": current_month_perf.to_dict()
    }
