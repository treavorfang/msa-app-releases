# controllers/inventory_controller.py
"""Inventory controller handling part look‑ups and stock updates.
It acts as a thin façade over an optional service layer; if the service
is not provided it falls back to direct ORM queries.
"""
from PySide6.QtCore import QObject, Signal

class InventoryController(QObject):
    """Controller for inventory‑related operations.

    Parameters
    ----------
    container: DependencyContainer
        The application‑wide container that may expose an ``inventory_service``.
    """
    def __init__(self, container):
        """Create the controller and optionally bind a service.

        The ``inventory_service`` attribute (if present) should implement a
        ``get_part(part_id)`` method.  When absent, the controller uses the
        Peewee ``Part`` model directly.
        """
        super().__init__()
        self.container = container
        # Optional service layer for inventory operations
        self.inventory_service = getattr(container, "inventory_service", None)
    def get_part(self, part_id):
        """Return a :class:`models.part.Part` instance for ``part_id``.

        The method first checks whether an ``inventory_service`` providing a
        ``get_part`` method is attached to the controller.  If not, it falls
        back to a direct Peewee lookup.  ``None`` is returned when the part
        cannot be found or an error occurs.
        """
        # Use service layer if available
        if self.inventory_service and hasattr(self.inventory_service, 'get_part'):
            return self.inventory_service.get_part(part_id)
        # Direct ORM lookup
        try:
            from models.part import Part
            return Part.get_by_id(part_id)
        except Exception:
            return None


    def add_part(self, part_data):
        pass

    def update_stock(self, part_id, quantity_change):
        pass

    def _check_low_stock(self):
        pass

    def get_low_stock_items(self):
        pass