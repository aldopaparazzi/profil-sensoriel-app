# pipeline/types.py

from typing import TypedDict, Optional


class NormResult(TypedDict):
    m: Optional[float]
    sigma: Optional[float]
    age_group_used: Optional[str]
    warning: Optional[str]
    error: Optional[str]