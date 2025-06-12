from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.amenity_schema import AmenityBase


class RoomBase(BaseModel):
    number_room: int = Field(..., gt=0, description="Numero unico de habitacion")  # Corregido: number_room
    type: str = Field(..., example="deluxe")
    price_per_night: float
    capacity: int


class RoomCreate(RoomBase):
    amenities: list[AmenityBase] = []
    description: Optional[str] = None
    images: list[str] = []
    availability: Optional[bool] = True


class RoomUpdate(BaseModel):
    number_room: Optional[int] = None
    type: Optional[str] = None
    price_per_night: Optional[float] = None
    capacity: Optional[int] = None
    amenities: Optional[List[AmenityBase]] = None
    description: Optional[str] = None
    images: Optional[List[str]] = None
    availability: Optional[bool] = None

class RoomResponse(RoomBase):
    id: str
    availability: bool  # Corregido: availability (igual que en el modelo)
    amenities: list[AmenityBase]
    description: Optional[str] = None  # Agregado
    images: list[str] = []  # Agregado

    class Config:
        from_attributes = True  # Corregido: from_attributes