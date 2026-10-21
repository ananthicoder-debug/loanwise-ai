"""models/loan.py  -  Pydantic schemas for loan-related requests."""

from pydantic import BaseModel
from typing import Optional, List


class LoanApplicationRequest(BaseModel):
    loan_amount: float
    loan_tenure: int
    loan_category: str
    purpose: Optional[str] = ""
    coapplicant: Optional[bool] = False
    coapplicant_income: Optional[float] = 0


class LenderCreateRequest(BaseModel):
    lender_code: Optional[str] = None
    lender_name: str
    lender_type: str = "Bank"
    headquarters_city: Optional[str] = ""
    state: Optional[str] = ""
    official_website: Optional[str] = ""
    verification_status: Optional[str] = "Not_Publicly_Specified"
    dataset_type: Optional[str] = "Verified_Product_Catalogue"
    status: Optional[str] = "active"


class LoanProductCreateRequest(BaseModel):
    lender_id: str
    product_code: Optional[str] = None
    product_name: str
    loan_category: str
    min_amount: float
    max_amount: float
    interest_rate_min: float
    interest_rate_max: float
    min_tenure: int
    max_tenure: int
    processing_fee: Optional[str] = "Not publicly specified"
    minimum_income: Optional[float] = 0
    minimum_cibil: Optional[int] = 0
    minimum_age: Optional[int] = 18
    maximum_age: Optional[int] = 70
    employment_required: Optional[str] = "Not publicly specified"
    collateral_required: Optional[str] = "No"
    coapplicant_allowed: Optional[str] = "Depends"
    benefits: Optional[List[str]] = []
    eligibility_conditions: Optional[List[str]] = []
    documents_required: Optional[str] = "Not publicly specified"
    purpose: Optional[str] = ""
    official_product_url: Optional[str] = ""
    source_date: Optional[str] = ""
    verification_status: Optional[str] = "Not_Publicly_Specified"
    dataset_type: Optional[str] = "Verified_Product_Catalogue"
    is_active: Optional[bool] = True


class LoanProductUpdateRequest(BaseModel):
    product_name: Optional[str] = None
    loan_category: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    interest_rate_min: Optional[float] = None
    interest_rate_max: Optional[float] = None
    min_tenure: Optional[int] = None
    max_tenure: Optional[int] = None
    processing_fee: Optional[str] = None
    minimum_income: Optional[float] = None
    minimum_cibil: Optional[int] = None
    benefits: Optional[List[str]] = None
    eligibility_conditions: Optional[List[str]] = None
    official_product_url: Optional[str] = None
    verification_status: Optional[str] = None
    is_active: Optional[bool] = None
