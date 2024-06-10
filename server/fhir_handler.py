# FHIR HANDLER

from fhir.resources.patient import Patient
from fhir.resources.bundle import Bundle
import json

def validate_fhir_data(fhir_json):
    try:
        # Parse FHIR JSON to ensure it's a valid FHIR resource
        resource = json.loads(fhir_json)
        
        # Here we're assuming the resource is a Patient, modify as necessary for other resource types
        patient = Patient(**resource)
        return True, "Valid FHIR Data"
    except Exception as e:
        return False, str(e)
