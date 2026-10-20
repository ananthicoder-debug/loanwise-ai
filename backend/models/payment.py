"""models/payment.py — Pydantic schemas for active loans and payments."""

from pydantic import BaseModel
from typing import Optional


class ActiveLoanCreateRequest(BaseModel):
    product_id: str
    recommendation_id: Optional[str] = None
    application_id: Optional[str] = None
    actual_amount: float
    interest_rate: float
    tenure_months: int
    start_date: str          # YYYY-MM-DD
    first_due_date: str      # YYYY-MM-DD


class MarkPaidRequest(BaseModel):
    amount_paid: Optional[float] = None
    payment_date: Optional[str] = None   # YYYY-MM-DD, defaults to today
