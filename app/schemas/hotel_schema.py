from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from app.schemas.amenity_schema import AmenityBase


class AddressBase(BaseModel):
    street: str
    city: str
    state: str
    country: str
    postal_code: str


class HotelBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    address: AddressBase
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None


class HotelCreate(HotelBase):
    amenities: List[AmenityBase] = []
    images: List[str] = []


class HotelResponse(HotelBase):
    id: str
    rating: float = 0.0
    amenities: List[AmenityBase]
    images: List[str] = []
    rooms: List[str] = []  # Lista de IDs de habitaciones

    class Config:
        from_attributes = True


class HotelListResponse(BaseModel):
    id: str
    name: str
    address: AddressBase
    rating: float
    images: List[str] = []

    class Config:
        from_attributes = True