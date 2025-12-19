# src/app/interfaces/ipart_service.py
from typing import Optional, List
from models.part import Part

class IPartService:
    def create_part(self, brand: str, category: str, name: str, cost: float, 
                   stock: int = 0, sku: Optional[str] = None, 
                   model_compatibility: Optional[str] = None, 
                   min_stock_level: int = 0, barcode: Optional[str] = None) -> Part:
        raise NotImplementedError
    
    def get_part_by_id(self, part_id: int) -> Optional[Part]:
        raise NotImplementedError
    
    def get_part_by_sku(self, sku: str) -> Optional[Part]:
        raise NotImplementedError
    
    def get_part_by_barcode(self, barcode: str) -> Optional[Part]:
        raise NotImplementedError
    
    def update_part(self, part_id: int, **kwargs) -> Optional[Part]:
        raise NotImplementedError
    
    def update_stock(self, part_id: int, quantity: int) -> Optional[Part]:
        raise NotImplementedError
    
    def search_parts(self, query: str, limit: int = 100) -> List[Part]:
        raise NotImplementedError
    
    def get_parts_by_category(self, category: str) -> List[Part]:
        raise NotImplementedError
    
    def get_all_parts(self) -> List[Part]:
        raise NotImplementedError
    
    def get_low_stock_parts(self, threshold: int = 5) -> List[Part]:
        raise NotImplementedError
    
    def get_out_of_stock_parts(self) -> List[Part]:
        raise NotImplementedError
    
    def get_total_inventory_value(self) -> float:
        raise NotImplementedError