# models.py

from datetime import date
from pydantic import BaseModel

class PatientAuthRequest(BaseModel):
    first_name: str
    last_name: str
    dob: date

class AuthResponse(BaseModel):
    authenticated: bool

class PatientBase(BaseModel):
    first_name: str
    last_name: str
    dob: date
    phone_number: str

class PatientCreate(PatientBase):
    pass

class Patient(PatientBase):
    patient_id: str

class PatientUpdate(PatientBase):
    pass