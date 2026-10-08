from dataclasses import dataclass, field
from typing import List


@dataclass
class Surgery:
    id: str
    procedure: str
    specialty: str
    priority: str
    duration: int
    surgeon: str
    anesthetist: str
    required_equipment: List[str] = field(default_factory=list)
    recovery_beds: int = 1
    preferred_start: int = 0
    preferred_end: int = 600


@dataclass
class OperatingRoom:
    id: str
    specialties: List[str]
    available_start: int = 0
    available_end: int = 600
    unavailable_periods: List[dict] = field(default_factory=list)


@dataclass
class Staff:
    id: str
    role: str
    available_start: int = 0
    available_end: int = 600


@dataclass
class Equipment:
    id: str
    equipment_type: str
    available_start: int = 0
    available_end: int = 600


@dataclass
class RecoveryBed:
    id: str
    available: bool = True