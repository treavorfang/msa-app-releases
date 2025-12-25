from fastapi import APIRouter
from api.routes.auth import router as auth_router
from api.routes.tickets import router as tickets_router
from api.routes.inventory import router as inventory_router
from api.routes.stats import router as stats_router
from api.routes.customers import router as customers_router
from api.routes.technicians import router as technicians_router
from api.routes.metadata import router as metadata_router
from api.routes.devices import router as devices_router
from api.routes.invoices import router as invoices_router
from api.routes.financial import router as financial_router

router = APIRouter(prefix="/api")

router.include_router(auth_router, tags=["Authentication"])
router.include_router(tickets_router, prefix="/tickets", tags=["Tickets"])
router.include_router(inventory_router, prefix="/inventory", tags=["Inventory"])
router.include_router(stats_router, prefix="/stats", tags=["Statistics"])
router.include_router(customers_router, prefix="/customers", tags=["Customers"])
router.include_router(technicians_router, prefix="/technicians", tags=["Technicians"])
router.include_router(metadata_router, prefix="/metadata", tags=["Metadata"])
router.include_router(devices_router, prefix="/devices", tags=["Devices"])
router.include_router(invoices_router, prefix="/invoices", tags=["Invoices"])
router.include_router(financial_router, prefix="/financial", tags=["Financial"])
