from pydantic import BaseModel
from typing import List, Dict

class SummaryResponse(BaseModel):
    one_liner: str
    steps: List[str]
    inputs_outputs: List[str]
    caveats: List[str]
    next_steps: List[str]  # New field for developer guidance
    node_refs: List[Dict[str, str]]