from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class LegalSource:
    id: str
    jurisdiction: str
    authority: str
    title: str
    citation: Optional[str]
    date: Optional[str]
    provision: Optional[str]
    url: Optional[str]
    last_verified: Optional[str]
    text: str

    def to_dict(self):
        return asdict(self)
