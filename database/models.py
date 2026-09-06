"""
Simple dataclass model for an agent record.
No async, no pydantic — just a plain dataclass with a to_dict() helper.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Agent:
    """Represents one MahaRERA registered agent."""

    agent_id: str

    # Identity
    agent_name: str = ""
    first_name: str = ""
    middle_name: str = ""
    last_name: str = ""
    father_name: str = ""

    # Registration
    certificate_no: str = ""
    registration_date: str = ""
    validity_end_date: str = ""
    status: str = ""

    # Contact
    mobile: str = ""
    alternate_mobile: str = ""
    office_phone: str = ""
    email: str = ""
    website: str = ""

    # Address
    unit_number: str = ""
    building_name: str = ""
    street_name: str = ""
    locality: str = ""
    landmark: str = ""
    city: str = ""
    taluka: str = ""
    district: str = ""
    state: str = "Maharashtra"
    pincode: str = ""
    address: str = ""  # Full combined address

    # Metadata
    collection_status: str = "pending"    # pending | collected | failed
    failure_reason: Optional[str] = None
    collected_at: Optional[str] = None
    created_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat(timespec="seconds")
    )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.middle_name, self.last_name]
        name = " ".join(p for p in parts if p).strip()
        return name or self.agent_name

    def merge(self, data: dict) -> None:
        """
        Update fields from a dict (e.g. scraped detail data).
        Only updates fields that exist on this dataclass and whose
        incoming value is non-empty.
        """
        for key, val in data.items():
            if hasattr(self, key) and val not in (None, ""):
                setattr(self, key, str(val).strip())
