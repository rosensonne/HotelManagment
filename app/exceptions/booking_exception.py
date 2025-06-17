from fastapi import HTTPException, status

class BookingException(HTTPException):
    """Excepción base para errores relacionados con reservas"""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class RoomNotAvailableException(BookingException):
    """Excepción cuando una habitación no está disponible"""
    def __init__(self, room_id: str, check_in: str, check_out: str):
        detail = f"La habitación {room_id} no está disponible del {check_in} al {check_out}"
        super().__init__(detail)

class ReservationNotFoundException(HTTPException):
    """Excepción cuando no se encuentra una reserva"""
    def __init__(self, reservation_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reserva {reservation_id} no encontrada"
        )

class ReservationNotOwnedException(HTTPException):
    """Excepción cuando un usuario intenta acceder a una reserva que no le pertenece"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a esta reserva"
        )

class InvalidReservationStatusException(BookingException):
    """Excepción para transiciones de estado inválidas"""
    def __init__(self, current_status: str, attempted_status: str):
        detail = f"No se puede cambiar de estado '{current_status}' a '{attempted_status}'"
        super().__init__(detail)

class ReservationCannotBeCancelledException(BookingException):
    """Excepción cuando una reserva no puede ser cancelada"""
    def __init__(self, reason: str = "La reserva no puede ser cancelada en este momento"):
        super().__init__(reason)

class InvalidDateRangeException(BookingException):
    """Excepción para rangos de fechas inválidos"""
    def __init__(self, message: str = "Rango de fechas inválido"):
        super().__init__(message)

class MaximumStayExceededException(BookingException):
    """Excepción cuando se excede la estancia máxima permitida"""
    def __init__(self, max_days: int):
        detail = f"La estancia no puede exceder {max_days} días"
        super().__init__(detail)

class AdvanceBookingLimitException(BookingException):
    """Excepción cuando se intenta reservar con demasiada anticipación"""
    def __init__(self, max_advance_days: int):
        detail = f"No se pueden hacer reservas con más de {max_advance_days} días de anticipación"
        super().__init__(detail)

class PastDateBookingException(BookingException):
    """Excepción cuando se intenta reservar fechas pasadas"""
    def __init__(self):
        detail = "No se pueden hacer reservas para fechas pasadas"
        super().__init__(detail)

class ExtraServiceNotFoundException(HTTPException):
    """Excepción cuando no se encuentra un servicio extra"""
    def __init__(self, service_index: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Servicio extra en índice {service_index} no encontrado"
        )

class PaymentRequiredException(HTTPException):
    """Excepción cuando se requiere pago antes de confirmar"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Se requiere completar el pago antes de confirmar la reserva"
        )