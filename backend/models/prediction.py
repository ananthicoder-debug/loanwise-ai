"""
models/prediction.py
---------------------
Purpose:
    Response schemas for Model 1 (eligibility) and Model 2 (affordability)
    outputs, and for the combined recommendation record. Kept separate
    from user.py/loan.py because these describe ML OUTPUT shape, not
    input forms.
"""

from pydantic import BaseModel


class EligibilityResult(BaseModel):
    result: str  # "Eligible" | "Not Eligible"
    probability: float


class AffordabilityResult(BaseModel):
    result: str  # "Manageable" | "Not Manageable"
    probability: float
