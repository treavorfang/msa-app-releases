from fastapi import APIRouter
from typing import List
from services.part_service import PartService
from services.audit_service import AuditService

router = APIRouter()
audit_service = AuditService()
part_service = PartService(audit_service)

@router.get("/search")
async def search_inventory(q: str = "", category_id: int = None, supplier_id: int = None, limit: int = 20, skip: int = 0):
    """Search inventory by Name, SKU, or Barcode with filters."""
    # Use service for search logic and pagination
    results = part_service.search_parts(q, category_id, supplier_id, limit=limit, offset=skip)
    
    return [{
        "id": p.id,
        "name": p.name,
        "sku": p.sku,
        "brand": p.brand,
        "stock": p.current_stock,
        "price": float(p.cost_price)
    } for p in results]
