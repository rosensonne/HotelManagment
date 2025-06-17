from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, field_validator

class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class ExtraServiceBase(BaseModel):
    name: str
    price: float
    description: Optional[str] = None

class ExtraServiceCreate(ExtraServiceBase):
    pass

class ExtraServiceResponse(ExtraServiceBase):
    pass

class BookingBase(BaseModel):
    room_id: str
    start_time: datetime
    end_time: datetime

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, v, info):
        if info.data.get("start_time") and v <= info.data["start_time"]:
            raise ValueError("La fecha de salida debe ser posterior a la fecha de entrada.")
        return v

    @field_validator("start_time")
    @classmethod
    def validate_start_time(cls, v):
        if v < datetime.now():
            raise ValueError("La fecha de entrada no puede ser en el pasado.")
        return v

class BookingCreate(BookingBase):
    additional_services: List[ExtraServiceCreate] = []

class BookingUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    additional_services: Optional[List[ExtraServiceCreate]] = None

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, v, info):
        if v and info.data.get("start_time") and v <= info.data["start_time"]:
            raise ValueError("La fecha de salida debe ser posterior a la fecha de entrada.")
        return v

class BookingResponse(BookingBase):
    id: str
    user_id: str
    total_price: float
    status: BookingStatus

    class Config:
        from_attributes = True

class StatusHistory(BaseModel):
    status: BookingStatus
    date: datetime

class ReservationDetails(BookingResponse):
    room_name: str
    hotel_name: str
    extra_services: List[ExtraServiceResponse]
    status_history: List[StatusHistory]
    opinions: Optional[str] = None

class ReservationSummary(BaseModel):
    """Resumen para estadísticas y reportes"""
    total_reservations: int
    pending_reservations: int
    confirmed_reservations: int
    cancelled_reservations: int
    completed_reservations: int
    total_revenue: float

class AvailabilityCheck(BaseModel):
    room_id: str
    check_in: datetime
    check_out: datetime
    is_available: bool
    conflicting_reservations: List[str] = []

class ReservationFilter(BaseModel):
    """Filtros para búsqueda de reservas"""
    status: Optional[BookingStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    hotel_id: Optional[str] = None
    room_id: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None

# Esquemas adicionales para operaciones específicas
class ReservationConfirm(BaseModel):
    """Schema para confirmar una reserva"""
    payment_id: Optional[str] = None
    notes: Optional[str] = None

class ReservationCancel(BaseModel):
    """Schema para cancelar una reserva"""
    reason: Optional[str] = None
    refund_requested: bool = True

class BulkReservationResponse(BaseModel):
    """Respuesta para operaciones en lote"""
    successful: List[str]
    failed: List[dict]
    total_processed: int

class ReservationSearch(BaseModel):
    """Parámetros de búsqueda avanzada"""
    hotel_name: Optional[str] = None
    room_type: Optional[str] = None
    guest_name: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    status: Optional[List[BookingStatus]] = None
    min_nights: Optional[int] = None
    max_nights: Optional[int] = None