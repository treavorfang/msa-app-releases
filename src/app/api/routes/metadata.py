from fastapi import APIRouter
from config.config_loader import load_brands_config, load_phone_errors

router = APIRouter()

@router.get("/brands")
async def get_brands():
    """Get phone brands and models."""
    return load_brands_config()

@router.get("/errors")
async def get_errors():
    """Get common phone error categories."""
    return load_phone_errors()

@router.get("/categories")
async def get_categories():
    """Get all part categories."""
    from models.category import Category
    # Only get active and non-deleted categories
    categories = Category.select().where(
        Category.is_active == True,
        Category.deleted_at.is_null()
    ).order_by(Category.name)
    
    return [{"id": c.id, "name": c.name} for c in categories]

@router.get("/suppliers")
async def get_suppliers():
    """Get all active suppliers."""
    from models.supplier import Supplier
    suppliers = Supplier.select().order_by(Supplier.name)
    return [{"id": s.id, "name": s.name} for s in suppliers]
