from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime

class EventPayload(BaseModel):
    # flexible payload
    __root__: Dict[str, Any] = {}

class Event(BaseModel):
    topic: str = Field(..., min_length=1)
    event_id: str = Field(..., min_length=1)
    timestamp: datetime
    source: str = Field(..., min_length=1)
    payload: Dict[str, Any] = {}
