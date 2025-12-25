from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import datetime, date, timedelta
from services.financial_service import FinancialService
from repositories.financial_repository import FinancialRepository
from services.audit_service import AuditService
from models.user import User

# Service Initialization
repository = FinancialRepository()
audit_service = AuditService()
service = FinancialService(repository, audit_service)

router = APIRouter()

# --- Pydantic Models ---

class TransactionCreate(BaseModel):
    amount: float
    type: str # 'income' or 'expense'
    category_id: int
    date: Optional[str] = None # ISO Format
    description: Optional[str] = ""
    payment_method: str = "cash"
    
class TransactionParam(BaseModel):
    id: int
    amount: float
    type: str
    category_name: str
    category_color: str
    description: str
    date: str
    payment_method: str

class CategoryResponse(BaseModel):
    id: int
    name: str
    color: str
    is_income: bool

class DashboardSummary(BaseModel):
    total_income: float
    total_expense: float
    net_profit: float
    recent_transactions: List[TransactionParam]

async def get_current_user(x_user_id: Optional[int] = Header(None, alias="X-User-ID")):
    if x_user_id:
        return User.get_or_none(User.id == x_user_id)
    return None

# --- Routes ---

@router.get("/summary")
async def get_summary(days: int = 30):
    """Get financial summary for the dashboard."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    summary = service.get_dashboard_summary(start_date, end_date)
    recent = service.get_recent_transactions(limit=20)
    
    recent_list = []
    for t in recent:
        recent_list.append({
            "id": t.id,
            "amount": float(t.amount),
            "type": t.type,
            "category_name": t.category_name,
            "category_color": getattr(t, 'category_color', '#666666'),
            "description": t.description or "",
            "date": t.date.strftime("%Y-%m-%d"),
            "payment_method": t.payment_method
        })
        
    return {
        "summary": summary,
        "recent_transactions": recent_list
    }

@router.get("/transactions")
async def list_transactions(limit: int = 50, skip: int = 0, type: Optional[str] = None):
    """List recent transactions with pagination and filtering."""
    recent = service.get_recent_transactions(limit=limit, offset=skip, filter_type=type)
    results = []
    for t in recent:
        results.append({
            "id": t.id,
            "amount": float(t.amount),
            "type": t.type,
            "category_name": t.category_name,
            "category_color": getattr(t, 'category_color', '#666666'),
            "description": t.description or "",
            "date": t.date.strftime("%Y-%m-%d %H:%M"),
            "payment_method": t.payment_method
        })
    return results

@router.post("/transactions")
async def add_transaction(req: TransactionCreate, user: Optional[User] = Depends(get_current_user)):
    """Add a new transaction."""
    try:
        date_obj = datetime.now()
        if req.date:
            try:
                date_obj = datetime.fromisoformat(req.date.replace("Z", "+00:00"))
            except:
                pass
                
        service.add_transaction(
            amount=req.amount,
            type=req.type,
            category_id=req.category_id,
            date_obj=date_obj,
            description=req.description,
            payment_method=req.payment_method,
            current_user=user,
            ip_address="Mobile App"
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/transactions/{id}")
async def delete_transaction(id: int, user: Optional[User] = Depends(get_current_user)):
    """Delete a transaction."""
    success = service.delete_transaction(id, current_user=user, ip_address="Mobile App")
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"status": "success"}

@router.get("/categories")
async def get_categories(type: Optional[str] = None):
    """Get expense categories."""
    is_income = None
    if type == 'income':
        is_income = True
    elif type == 'expense':
        is_income = False
        
    cats = service.get_categories(is_income)
    return [{
        "id": c.id,
        "name": c.name,
        "color": c.color,
        "is_income": c.is_income
    } for c in cats]
