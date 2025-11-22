"""Tools package."""
from .triage_tool import triage_patient_tool
from .geo_tool import find_hospitals_tool
from .bed_tool import allocate_patient_beds_tool

__all__ = [
    "triage_patient_tool",
    "find_hospitals_tool",
    "allocate_patient_beds_tool"
]
