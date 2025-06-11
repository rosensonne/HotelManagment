from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    CASH = "cash"
    TRANSFER = "transfer"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class PaymentBase(BaseModel):
    reservation_id: str
    amount: float = Field(..., gt=0)
    method: PaymentMethod

class PaymentResponse(PaymentBase):
    id: str
    status: PaymentStatus
    transaction_date: datetime
    class Config:
        from_attributes = True