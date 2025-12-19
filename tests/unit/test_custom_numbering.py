import pytest
import os
import sys
from datetime import datetime
from peewee import SqliteDatabase

# Ensure project src is on path for imports in models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "app"))

from models.business_settings import BusinessSettings
from models.invoice import Invoice
from models.ticket import Ticket
from models.purchase_order import PurchaseOrder
from dtos.business_settings_dto import BusinessSettingsDTO
from models.user import User

# Use in-memory database for testing
test_db = SqliteDatabase(':memory:')

@pytest.fixture(scope='module', autouse=True)
def setup_db():
    # Bind models to test_db
    models = [BusinessSettings, Invoice, Ticket, PurchaseOrder, User]
    # Important: bind to test_db BEFORE connecting
    test_db.bind(models, bind_refs=False, bind_backrefs=False)
    test_db.connect()
    test_db.create_tables(models)
    yield
    test_db.drop_tables(models)
    test_db.close()

@pytest.fixture
def setup_settings():
    # Clear existing settings and create fresh one
    BusinessSettings.delete().execute()
    return BusinessSettings.create(
        business_name="Test Shop",
        invoice_number_format="INV-{branch}-{date}-{seq}",
        ticket_number_format="TKT-{branch}-{seq}",
        po_number_format="PO-{seq}-TEST",
        invoice_terms="Term 1\nTerm 2"
    )

def test_invoice_number_generation(setup_settings):
    today = datetime.now().strftime("%y%m%d")
    inv_num = Invoice.generate_invoice_number(branch_id=5)
    assert inv_num == f"INV-5-{today}-0001"
    
    # Test different format
    setup_settings.invoice_number_format = "SHOP5-{seq}"
    setup_settings.save()
    
    inv_num = Invoice.generate_invoice_number(branch_id=5)
    assert inv_num == "SHOP5-0001"

def test_ticket_number_generation(setup_settings):
    # Default sequence starts at 1
    tkt_num = Ticket.generate_ticket_number(branch_id=1)
    assert tkt_num == "TKT-1-0001"
    
    # Test custom format
    setup_settings.ticket_number_format = "REPAIR-{branch}-{date}-{seq}"
    setup_settings.save()
    today = datetime.now().strftime("%y%m%d")
    
    tkt_num = Ticket.generate_ticket_number(branch_id=2)
    assert tkt_num == f"REPAIR-2-{today}-0001"

def test_po_number_generation(setup_settings):
    po_num = PurchaseOrder.generate_po_number(branch_id=1)
    assert po_num == "PO-0001-TEST"

def test_settings_dto_new_fields(setup_settings):
    dto = BusinessSettingsDTO.from_model(setup_settings)
    assert dto.invoice_number_format == "INV-{branch}-{date}-{seq}"
    assert dto.invoice_terms == "Term 1\nTerm 2"
    
    d = dto.to_dict()
    assert d['invoice_number_format'] == "INV-{branch}-{date}-{seq}"
    assert d['invoice_terms'] == "Term 1\nTerm 2"
