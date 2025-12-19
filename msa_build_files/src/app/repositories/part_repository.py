"""Part Repository - Part Inventory Data Access Layer.

This repository handles all database operations for Part entities.
Features include inventory management, stock tracking, and searching.
"""

from typing import Optional, List
from peewee import DoesNotExist, fn
from models.part import Part
from models.category import Category


class PartRepository:
    """Repository for Part data access operations."""
    
    def create_part(self, brand: str, category_name: str, name: str, cost_price: float, 
                   current_stock: int = 0, sku: Optional[str] = None, 
                   model_compatibility: Optional[str] = None, 
                   min_stock_level: int = 0, barcode: Optional[str] = None,
                   is_active: bool = True) -> Part:
        """Create a new part.
        
        Args:
            brand: Brand of the part
            category_name: Name of the category (created if not exists)
            name: Name of the part
            cost_price: Cost price
            current_stock: Initial stock level
            sku: Stock Keeping Unit identifier (optional)
            model_compatibility: Compatible models (optional)
            min_stock_level: Minimum stock warning level
            barcode: Barcode string (optional)
            is_active: Whether the part is active
        """
        # Get or create category
        category, _ = Category.get_or_create(name=category_name)
        
        return Part.create(
            brand=brand,
            category=category,
            name=name,
            cost_price=cost_price,
            current_stock=current_stock,
            sku=sku,
            model_compatibility=model_compatibility,
            min_stock_level=min_stock_level,
            barcode=barcode,
            is_active=is_active
        )
    
    def get_part_by_id(self, part_id: int) -> Optional[Part]:
        """Get part by ID."""
        try:
            return Part.get_by_id(part_id)
        except DoesNotExist:
            return None
    
    def get_part_by_sku(self, sku: str) -> Optional[Part]:
        """Get part by SKU."""
        try:
            return Part.get(Part.sku == sku)
        except DoesNotExist:
            return None
    
    def get_part_by_barcode(self, barcode: str) -> Optional[Part]:
        """Get part by barcode."""
        try:
            return Part.get(Part.barcode == barcode)
        except DoesNotExist:
            return None
    
    def update_part(self, part_id: int, **kwargs) -> Optional[Part]:
        """Update part with new values."""
        try:
            part = Part.get_by_id(part_id)
            for key, value in kwargs.items():
                if (key == 'category_name' or key == 'category') and value:
                    # Handle category lookup/creation
                    category, _ = Category.get_or_create(name=value)
                    part.category = category
                elif key == 'cost':
                    # Map 'cost' to 'cost_price'
                    part.cost_price = value
                elif key == 'stock':
                    # Map 'stock' to 'current_stock'
                    part.current_stock = value
                else:
                    # Handle other fields directly
                    if hasattr(part, key):
                        setattr(part, key, value)
            part.save()
            return part
        except DoesNotExist:
            return None
    
    def update_stock(self, part_id: int, quantity: int) -> Optional[Part]:
        """Update stock level by adding quantity (can be negative)."""
        try:
            part = Part.get_by_id(part_id)
            part.current_stock += quantity
            part.save()
            return part
        except DoesNotExist:
            return None
    
    def search_parts(self, query: str, limit: int = 100) -> List[Part]:
        """Search parts by brand, category, name, SKU, compatibility, or barcode."""
        return list(
            Part.select().where(
                (Part.brand.contains(query)) |
                (Part.category.name.contains(query)) |
                (Part.name.contains(query)) |
                (Part.sku.contains(query)) |
                (Part.model_compatibility.contains(query)) |
                (Part.barcode.contains(query))
            ).limit(limit)
        )
    
    def get_parts_by_category(self, category_name: str) -> List[Part]:
        """Get all parts in a specific category."""
        return list(Part.select().join(Category).where(Category.name == category_name))
    
    def get_all_parts(self) -> List[Part]:
        """Get all parts."""
        return list(Part.select())
    
    def get_low_stock_parts(self, threshold: int = 5) -> List[Part]:
        """Get parts where stock is at or below threshold."""
        return list(Part.select().where(Part.current_stock <= threshold))
    
    def get_out_of_stock_parts(self) -> List[Part]:
        """Get parts with zero or negative stock."""
        return list(Part.select().where(Part.current_stock <= 0))
    
    def get_total_inventory_value(self) -> float:
        """Calculate total value of inventory (cost * stock)."""
        total = Part.select(fn.Sum(Part.cost_price * Part.current_stock)).scalar()
        return total or 0.0