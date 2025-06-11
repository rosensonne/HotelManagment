from typing import Optional

from pydantic import BaseModel


class AmenityBase(BaseModel):
    name: str
    icon: Optional[str] = None

class AmenityCreate(AmenityBase):
    pass

class AmenityResponse(AmenityBase):
    class Config:
        from_attributes = True