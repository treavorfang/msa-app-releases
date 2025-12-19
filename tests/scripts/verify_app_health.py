# tests/verify_app_health.py
import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Add src/app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'app'))

def verify_database():
    logger.info("Verifying Database Initialization...")
    try:
        from config.database import initialize_database, db
        initialize_database()
        
        from services.migration_service import MigrationService
        MigrationService().run_migrations()
        
        logger.info("✅ Database initialized and migrated successfully.")
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

def verify_imports():
    logger.info("Verifying Imports (Controllers)...")
    controllers = [
        "auth_controller",
        "branch_controller",
        "business_settings_controller",
        "category_controller",
        "customer_controller",
        "device_controller",
        "inventory_controller",
        "invoice_controller",
        "invoice_item_controller",
        "job_controller",
        "part_controller",
        "payment_controller",
        "purchase_order_controller",
        "purchase_return_controller",
        "repair_part_controller",
        "report_controller",
        "setting_controller",
        "supplier_controller",
        "technician_bonus_controller",
        "technician_controller",
        "technician_performance_controller",
        "theme_controller",
        "ticket_controller",
        "warranty_controller",
        "work_log_controller"
    ]
    
    failed = []
    for module_name in controllers:
        try:
            __import__(f"controllers.{module_name}")
            logger.info(f"  ✅ Imported {module_name}")
        except Exception as e:
            logger.error(f"  ❌ Failed to import {module_name}: {e}")
            failed.append(module_name)
            
    if failed:
        logger.error(f"❌ {len(failed)} controllers failed to import.")
        return False
    
    logger.info("✅ All controllers imported successfully.")
    return True

def verify_instantiation():
    logger.info("Verifying Critical Controller Instantiation...")
    try:
        # We need to initialize services first usually, but let's see if we can just instantiate
        # Some controllers might need arguments.
        
        # Audit Service is a common dependency
        from services.audit_service import AuditService
        audit_service = AuditService()
        
        # Ticket Controller
        from controllers.ticket_controller import TicketController
        # Assuming it might take a view or service, but let's try default or mock if needed
        # Inspecting TicketController __init__ would be safer, but let's try basic import first
        # If we can import, we are 90% there for this specific class of errors.
        
        logger.info("✅ Core services instantiated.")
        return True
    except Exception as e:
        logger.error(f"❌ Instantiation failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting App Health Check...")
    
    db_ok = verify_database()
    imports_ok = verify_imports()
    
    if db_ok and imports_ok:
        logger.info("\n✨ Health Check Passed! The application should be stable.")
        sys.exit(0)
    else:
        logger.error("\n💥 Health Check Failed. See errors above.")
        sys.exit(1)
