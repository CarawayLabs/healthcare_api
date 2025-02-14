import os
import csv
import uuid
import threading
from datetime import date
from typing import List

from fastapi import FastAPI, HTTPException, Query
from models import PatientAuthRequest, AuthResponse, PatientCreate, Patient, PatientUpdate

# Global configuration
CSV_FILE = "patients.csv"
csv_lock = threading.Lock()

# Ensure the CSV file exists with a header row
def ensure_csv_exists():
    if not os.path.exists(CSV_FILE):
        with csv_lock, open(CSV_FILE, "w", newline="") as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=["patient_id", "first_name", "last_name", "dob", "phone_number"]
            )
            writer.writeheader()

ensure_csv_exists()

# Helper functions for CSV operations
def read_patients() -> List[dict]:
    """Read all patient records from the CSV file."""
    ensure_csv_exists()
    with csv_lock, open(CSV_FILE, "r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)

def write_patients(patients: List[dict]):
    """Write the entire patient list to the CSV file."""
    with csv_lock, open(CSV_FILE, "w", newline="") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=["patient_id", "first_name", "last_name", "dob", "phone_number"]
        )
        writer.writeheader()
        writer.writerows(patients)

def append_patient(patient: dict):
    """Append a new patient record to the CSV file."""
    with csv_lock, open(CSV_FILE, "a", newline="") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=["patient_id", "first_name", "last_name", "dob", "phone_number"]
        )
        writer.writerow(patient)

def get_patient_by_id(patient_id: str) -> dict:
    """Find a patient by patient_id."""
    patients = read_patients()
    for patient in patients:
        if patient["patient_id"] == patient_id:
            return patient
    return None

# Initialize FastAPI app
app = FastAPI(title="Healthcare API")

# -----------------------
# Endpoint 1: Patient Authentication
# -----------------------
@app.post("/authenticate/patient", response_model=AuthResponse)
def authenticate_patient(auth: PatientAuthRequest):
    """
    Authenticates a patient. Currently, this endpoint always returns true.
    In the future, add logic to verify the provided patient details.
    """
    return AuthResponse(authenticated=True)

# -----------------------
# CRUD Endpoints for Patient Object
# -----------------------

# CREATE: Add a new patient
@app.post("/patient", response_model=dict)
def create_patient(patient: PatientCreate):
    """
    Creates a new patient record.
    Generates a UUID as the patient_id, appends the record to the CSV file,
    and returns the generated patient_id.
    """
    new_id = str(uuid.uuid4())
    patient_data = patient.dict()
    # Convert the dob to an ISO string for CSV storage.
    patient_data["dob"] = patient_data["dob"].isoformat()
    patient_record = {"patient_id": new_id, **patient_data}
    append_patient(patient_record)
    return {"patient_id": new_id}

# READ: Get a patient by patient_id
@app.get("/patient", response_model=Patient)
def read_patient(patient_id: str = Query(..., description="The UUID of the patient")):
    """
    Retrieves a patient record based on the provided patient_id.
    Raises a 404 HTTPException if the patient is not found.
    """
    patient_record = get_patient_by_id(patient_id)
    if not patient_record:
        raise HTTPException(status_code=404, detail="Patient not found")
    # Convert the stored ISO date string back into a date object.
    patient_record["dob"] = date.fromisoformat(patient_record["dob"])
    return patient_record

# READ: Get all patients
@app.get("/patients", response_model=List[Patient])
def read_patients_endpoint():
    """
    Returns a list of all patient records.
    """
    patients = read_patients()
    for patient in patients:
        patient["dob"] = date.fromisoformat(patient["dob"])
    return patients

# UPDATE: Update an existing patient record
@app.put("/patient", response_model=dict)
def update_patient(patient_update: PatientUpdate, patient_id: str = Query(..., description="The UUID of the patient to update")):
    """
    Updates a patient record with the provided patient_id.
    If the patient does not exist, returns a 404 error.
    """
    patients = read_patients()
    updated = False
    for patient in patients:
        if patient["patient_id"] == patient_id:
            updated_data = patient_update.dict()
            updated_data["dob"] = updated_data["dob"].isoformat()
            patient.update(updated_data)
            updated = True
            break
    if not updated:
        raise HTTPException(status_code=404, detail="Patient not found")
    write_patients(patients)
    return {"success": True}

# DELETE: Remove a patient record
@app.delete("/patient", response_model=dict)
def delete_patient(patient_id: str = Query(..., description="The UUID of the patient to delete")):
    """
    Deletes a patient record by patient_id.
    Returns a 404 error if the patient does not exist.
    """
    patients = read_patients()
    new_patients = [patient for patient in patients if patient["patient_id"] != patient_id]
    if len(new_patients) == len(patients):
        raise HTTPException(status_code=404, detail="Patient not found")
    write_patients(new_patients)
    return {"success": True}