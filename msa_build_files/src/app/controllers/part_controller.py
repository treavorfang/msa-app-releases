# src/app/controllers/part_controller.py
from typing import Optional, List
from dtos.part_dto import PartDTO
from interfaces.ipart_service import IPartService

from PySide6.QtCore import QObject, Signal

class PartController(QObject):
    data_changed = Signal()

    def __init__(self, part_service: IPartService):
        super().__init__()
        self._service = part_service

    def create_part(self, brand: str, category: str, name: str, cost: float, 
                   stock: int = 0, sku: Optional[str] = None, 
                   model_compatibility: Optional[str] = None, 
                   min_stock_level: int = 0, barcode: Optional[str] = None,
                   is_active: bool = True) -> PartDTO:
        """Create a new inventory part"""
        if cost <= 0:
            raise ValueError("Cost must be positive")
        if stock < 0:
            raise ValueError("Stock cannot be negative")
        if min_stock_level < 0:
            raise ValueError("Minimum stock level cannot be negative")
            
        part = self._service.create_part(
            brand=brand,
            category=category,
            name=name,
            cost=cost,
            stock=stock,
            sku=sku,
            model_compatibility=model_compatibility,
            min_stock_level=min_stock_level,
            barcode=barcode,
            is_active=is_active
        )
        self.data_changed.emit()
        return part

    def get_part(self, part_id: int) -> Optional[PartDTO]:
        """Get a part by its ID"""
        return self._service.get_part_by_id(part_id)

    def get_part_by_sku(self, sku: str) -> Optional[PartDTO]:
        """Get a part by its SKU"""
        return self._service.get_part_by_sku(sku)

    def update_part(self, part_id: int, **kwargs) -> Optional[PartDTO]:
        """Update part attributes"""
        if 'cost' in kwargs and kwargs['cost'] <= 0:
            raise ValueError("Cost must be positive")
        if 'stock' in kwargs and kwargs['stock'] < 0:
            raise ValueError("Stock cannot be negative")
        if 'min_stock_level' in kwargs and kwargs['min_stock_level'] < 0:
            raise ValueError("Minimum stock level cannot be negative")
            
        part = self._service.update_part(part_id, **kwargs)
        if part:
            self.data_changed.emit()
        return part

    def update_stock(self, part_id: int, quantity: int) -> Optional[PartDTO]:
        """Adjust inventory stock (positive to add, negative to subtract)"""
        part = self._service.update_stock(part_id, quantity)
        if part:
            self.data_changed.emit()
        return part

    def search_parts(self, query: str, limit: int = 100) -> List[PartDTO]:
        """Search parts by brand, category, name, or SKU"""
        return self._service.search_parts(query, limit)

    def get_parts_by_category(self, category: str) -> List[PartDTO]:
        """Get all parts in a specific category"""
        return self._service.get_parts_by_category(category)
    
    def get_all_parts(self) -> List[PartDTO]:
        """Get all parts"""
        return self._service.get_all_parts()
    
    def get_low_stock_parts(self, threshold: int = 5) -> List[PartDTO]:
        """Get parts with low stock"""
        return self._service.get_low_stock_parts(threshold)
    
    def get_out_of_stock_parts(self) -> List[PartDTO]:
        """Get out of stock parts"""
        return self._service.get_out_of_stock_parts()
    
    def get_total_inventory_value(self) -> float:
        """Get total inventory value"""
        return self._service.get_total_inventory_value()