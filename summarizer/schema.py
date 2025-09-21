from pydantic import BaseModel
from typing import List, Dict

class SummaryResponse(BaseModel):
    one_liner: str
    steps: List[str]
    inputs_outputs: List[str]
    caveats: List[str]
    node_refs: List[Dict[str, str]]
