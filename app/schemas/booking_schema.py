from datetime import datetime
from enum import Enum

from pydantic import BaseModel, field_validator

from app.schemas.amenity_schema import AmenityBase


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class BookingBase(BaseModel):
    room_id: str
    user_id: str
    start_time: datetime
    end_time: datetime

    @field_validator("start_time")
    def validate_start_time(cls, v, values):
        if "start_time" in values and v <= values["start_time"]:
            raise ValueError("La fecha de salida debe ser posterior a la fecha de entrada.")
        return v

class BookingCreate(BookingBase):
    additional_services: list[AmenityBase] = []

class BookingResponse(BookingBase):
    id: str
    total_price: float
    status: BookingStatus
    class Config:
        from_attributes = True