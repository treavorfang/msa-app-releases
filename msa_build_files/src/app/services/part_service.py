"""PartService - Inventory Part Management Business Logic.

This service manages the inventory of parts, including creation, updates,
stock tracking, price history, and inventory logging.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from models.part import Part
from interfaces.ipart_service import IPartService
from repositories.part_repository import PartRepository
from repositories.price_history_repository import PriceHistoryRepository
from repositories.inventory_log_repository import InventoryLogRepository
from repositories.inventory_log_repository import InventoryLogRepository
from services.audit_service import AuditService
from dtos.part_dto import PartDTO


class PartService(IPartService):
    """Service class for Part operations."""
    
    def __init__(self, audit_service: AuditService):
        """Initialize PartService.
        
        Args:
            audit_service: Service for logging security/audit events
        """
        self._audit_service = audit_service
        self._repository = PartRepository()
        self._price_history_repository = PriceHistoryRepository()
        self._inventory_log_repository = InventoryLogRepository()

    def create_part(self, brand: str, category: str, name: str, cost: float, 
                   stock: int = 0, sku: Optional[str] = None, 
                   model_compatibility: Optional[str] = None, 
                   min_stock_level: int = 0, barcode: Optional[str] = None,
                   is_active: bool = True) -> PartDTO:
        """Create a new part.
        
        Also initializes price history and logs the creation.
        """
        part = self._repository.create_part(
            brand=brand,
            category_name=category,
            name=name,
            cost_price=cost,
            current_stock=stock,
            sku=sku,
            model_compatibility=model_compatibility,
            min_stock_level=min_stock_level,
            barcode=barcode,
            is_active=is_active
        )
        
        self._audit_service.log_action(
            user=None,  # TODO: Pass actual user when available
            action="create",
            table_name="parts",
            new_data={
                "part_id": part.id,
                "brand": brand,
                "category": category,
                "name": name,
                "cost_price": float(cost),
                "current_stock": stock,
                "sku": part.sku,
                "barcode": part.barcode
            }
        )
        
        # Log initial price in price history
        self._price_history_repository.create_price_history_entry(
            part_id=part.id,
            old_price=0.00,
            new_price=float(cost),
            change_reason="Initial price"
        )
        
        return PartDTO.from_model(part)
    
    def get_part_by_id(self, part_id: int) -> Optional[PartDTO]:
        """Get a part by ID."""
        part = self._repository.get_part_by_id(part_id)
        return PartDTO.from_model(part) if part else None
    
    def get_part_by_sku(self, sku: str) -> Optional[PartDTO]:
        """Get a part by SKU."""
        part = self._repository.get_part_by_sku(sku)
        return PartDTO.from_model(part) if part else None
    
    def get_part_by_barcode(self, barcode: str) -> Optional[PartDTO]:
        """Get a part by barcode."""
        part = self._repository.get_part_by_barcode(barcode)
        return PartDTO.from_model(part) if part else None
    
    def update_part(self, part_id: int, user=None, **kwargs) -> Optional[PartDTO]:
        """Update a part's details.
        
        Handles:
        - Mapping input keys to model fields
        - Logging price changes explicitly
        - Logging stock adjustments to inventory log
        - Audit logging of the overall update
        """
        old_part = self._repository.get_part_by_id(part_id)
        if not old_part:
            return None
            
        # Map input keys to model fields for fetching old values
        # key in kwargs -> field in model
        field_map = {
            'cost': 'cost_price',
            'stock': 'current_stock',
            'category': 'category'
        }
        
        old_values = {}
        
        for key in kwargs.keys():
            # Determine the model field name
            model_field = field_map.get(key, key)
            
            if hasattr(old_part, model_field):
                val = getattr(old_part, model_field)
                
                # Serialize complex types
                if model_field == 'category' and val:
                    old_values[key] = val.name  # Store category name instead of object
                elif isinstance(val, Decimal):
                    old_values[key] = float(val)
                else:
                    old_values[key] = val

        part = self._repository.update_part(part_id, **kwargs)
        
        # Check if cost was updated and log price change
        if 'cost' in kwargs and part:
            new_cost = float(kwargs['cost'])
            old_cost = float(old_values.get('cost', 0))
            if new_cost != old_cost:
                self._price_history_repository.create_price_history_entry(
                    part_id=part_id,
                    old_price=old_cost,
                    new_price=new_cost,
                    change_reason=kwargs.get('price_change_reason', 'Price updated')
                )
                
        # Check if stock was updated and log inventory change
        if 'stock' in kwargs and part:
            new_stock = int(kwargs['stock'])
            old_stock = int(old_values.get('stock', 0))
            if new_stock != old_stock:
                diff = new_stock - old_stock
                self._inventory_log_repository.create_log({
                    'part': part_id,
                    'action_type': 'adjust',
                    'quantity': abs(diff),
                    'notes': kwargs.get('price_change_reason', 'Manual stock adjustment'),
                    'logged_by': user.id if hasattr(user, 'id') else user
                })
        
        if part:
            self._audit_service.log_action(
                user=user,
                action="update",
                table_name="parts",
                old_data={"part_id": part_id, **old_values},
                new_data={"part_id": part_id, **kwargs}
            )
        return PartDTO.from_model(part) if part else None
    
    def update_stock(self, part_id: int, quantity: int, 
                    reference_type: str = None, reference_id: int = None, 
                    notes: str = None, user=None) -> Optional[PartDTO]:
        """Update stock level (delta) and log the movement.
        
        Args:
            part_id: Part ID
            quantity: Amount to add (positive) or remove (negative)
            reference_type: Context (e.g. 'ticket', 'invoice')
            reference_id: Context ID
            notes: Optional notes
            user: User performing action
        """
        old_part = self._repository.get_part_by_id(part_id)
        if not old_part:
            return None
            
        part = self._repository.update_stock(part_id, quantity)
        
        if part:
            # Log to audit service
            self._audit_service.log_action(
                user=user,
                action="stock_update",
                table_name="parts",
                old_data={"part_id": part_id, "current_stock": old_part.current_stock},
                new_data={"part_id": part_id, "current_stock": part.current_stock}
            )
            
            # Log to inventory log
            action_type = 'in' if quantity > 0 else 'out'
            self._inventory_log_repository.create_log({
                'part': part_id,
                'action_type': action_type,
                'quantity': abs(quantity),
                'reference_type': reference_type,
                'reference_id': reference_id,
                'notes': notes,
                'logged_by': user.id if hasattr(user, 'id') else user
            })
            
            
        return PartDTO.from_model(part) if part else None
    
    def search_parts(self, query: str, limit: int = 100) -> List[PartDTO]:
        """Search parts by name, SKU, or barcode."""
        parts = self._repository.search_parts(query, limit)
        return [PartDTO.from_model(p) for p in parts]
    
    def get_parts_by_category(self, category: str) -> List[PartDTO]:
        """Get all parts in a category."""
        parts = self._repository.get_parts_by_category(category)
        return [PartDTO.from_model(p) for p in parts]
    
    def get_all_parts(self) -> List[PartDTO]:
        """Get all parts."""
        parts = self._repository.get_all_parts()
        return [PartDTO.from_model(p) for p in parts]
    
    def get_low_stock_parts(self, threshold: int = 5) -> List[PartDTO]:
        """Get parts matching low stock criteria."""
        parts = self._repository.get_low_stock_parts(threshold)
        return [PartDTO.from_model(p) for p in parts]
    
    def get_out_of_stock_parts(self) -> List[PartDTO]:
        """Get parts that have 0 stock."""
        parts = self._repository.get_out_of_stock_parts()
        return [PartDTO.from_model(p) for p in parts]
    
    def get_total_inventory_value(self) -> float:
        """Calculate total value of inventory (cost * stock)."""
        return self._repository.get_total_inventory_value()