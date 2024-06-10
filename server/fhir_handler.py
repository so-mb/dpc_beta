# FHIR HANDLER

from fhir.resources.patient import Patient
from pydantic import ValidationError

def validate_fhir_data(data):
    try:
        patient = Patient.parse_raw(data)
        return True, "FHIR data is valid"
    except ValidationError as ve:
        return False, f"Invalid FHIR Data: {ve}"
    except Exception as e:
        return False, f"Invalid FHIR Data: {e}"
