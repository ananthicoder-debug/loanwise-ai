"""models/user.py  -  Pydantic request/response schemas for users."""

from pydantic import BaseModel, EmailStr
from typing import Optional


class Address(BaseModel):
    street: Optional[str] = ""
    city: Optional[str] = ""
    state: Optional[str] = ""
    pincode: Optional[str] = ""


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[Address] = None
    pan_number: Optional[str] = None
    aadhaar_last4: Optional[str] = None
    occupation_description: Optional[str] = None


class CreditProfileUpdateRequest(BaseModel):
    age: Optional[int] = 25
    education: Optional[str] = "Graduate"
    employment_type: Optional[str] = "Salaried"
    employer_category: Optional[str] = "Private"
    years_of_employment: Optional[float] = 1.0
    monthly_income: Optional[float] = 0
    annual_income: Optional[float] = 0
    dependents: Optional[int] = 0
    residence_type: Optional[str] = "Rented"
    cibil_score: Optional[int] = 650
    existing_loans: Optional[int] = 0
    existing_emi: Optional[float] = 0
    outstanding_debt: Optional[float] = 0
    credit_card_outstanding: Optional[float] = 0
    credit_utilization: Optional[float] = 0
    previous_loans: Optional[int] = 0
    missed_payments: Optional[int] = 0
    late_payments: Optional[int] = 0
    average_days_late: Optional[float] = 0
    coapplicant: Optional[bool] = False
    coapplicant_income: Optional[float] = 0
    # Legacy aliases kept for backward compatibility with old frontend
    current_emi: Optional[float] = None
    credit_history: Optional[str] = None
