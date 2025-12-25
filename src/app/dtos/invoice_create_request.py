from pydantic import BaseModel
from typing import Optional

class PaymentRequest(BaseModel):
    method: str
    amount: float
    notes: Optional[str] = None

class InvoiceCreateRequest(BaseModel):
    labor_override: Optional[float] = None
    payment: Optional[PaymentRequest] = None
