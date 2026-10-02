from pydantic import BaseModel
from typing import Dict, List, Optional


class CloudResource(BaseModel):
    id: str
    name: str
    resource_type: str
    provider: str
    region: str
    configuration: Dict
    tags: Optional[Dict[str, str]] = {}


class Infrastructure(BaseModel):
    resources: List[CloudResource]