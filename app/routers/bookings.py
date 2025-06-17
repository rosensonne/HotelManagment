from datetime import datetime
from typing import List, Optional

import status
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from mongoengine import ValidationError, DoesNotExist

from app.models.Booking import Booking, ExtraService, ReserveStatus
from app.models.Room import Room
from app.models.User import User
from app.schemas.booking_schema import (
    BookingCreate,
    BookingResponse,
    BookingUpdate,
    ExtraServiceCreate,
    ReservationDetails
)
from app.utils.auth import get_current_user
from app.exceptions.booking_exception import BookingException
from app.utils.email import send_confirmation_email
from app.utils.booking_utils import (
    validate_room_availability,
    calculate_total_price,
    can_cancel_reservation
)

router = APIRouter(prefix="/reservations", tags=["Reservations"])


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_reservation(
        reservation: BookingCreate,
        current_user: User = Depends(get_current_user)
):
    """
    Crea una nueva reserva validando disponibilidad y calculando precio total.
    """
    try:
        # 1. Validar que la habitación existe
        try:
            room = Room.objects.get(id=reservation.room_id)
        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Habitación no encontrada"
            )

        # 2. Validar fechas
        if reservation.start_time >= reservation.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha de salida debe ser posterior a la fecha de entrada"
            )

        if reservation.start_time < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pueden hacer reservas para fechas pasadas"
            )

        # 3. Validar disponibilidad de la habitación
        if not validate_room_availability(reservation.room_id, reservation.start_time, reservation.end_time):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="La habitación no está disponible en las fechas seleccionadas"
            )

        # 4. Preparar servicios extras
        extra_services = []
        if reservation.additional_services:
            for service in reservation.additional_services:
                extra_service = ExtraService(
                    name=service.name,
                    price=service.price,
                    description=service.description
                )
                extra_services.append(extra_service)

        # 5. Calcular precio total
        nights = (reservation.end_time.date() - reservation.start_time.date()).days
        total_price = calculate_total_price(room.price, extra_services, nights)

        # 6. Crear reserva
        booking = Booking(
            room=room,
            user=current_user,
            check_in=reservation.start_time,
            check_out=reservation.end_time,
            extra_services=extra_services,
            total=total_price,
            status=[ReserveStatus(reserve_status='pending')]
        )

        booking.save()

        # 7. Enviar email de confirmación
        try:
            send_confirmation_email(current_user.email, str(booking.id))
        except Exception as e:
            # Log error but don't fail the reservation
            print(f"Error sending confirmation email: {e}")

        return BookingResponse(
            id=str(booking.id),
            room_id=str(booking.room.id),
            user_id=str(booking.user.id),
            start_time=booking.check_in,
            end_time=booking.check_out,
            total_price=booking.total,
            status=booking.status[-1].reserve_status
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de validación: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get("/", response_model=List[BookingResponse])
async def get_user_reservations(
        current_user: User = Depends(get_current_user),
        status_filter: Optional[str] = None,
        limit: int = 10,
        skip: int = 0
):
    """
    Obtiene el historial de reservas del usuario autenticado.
    """
    try:
        # Construir filtros
        filters = {"user": current_user}

        if status_filter:
            filters["status__reserve_status"] = status_filter

        # Obtener reservas con paginación
        bookings = Booking.objects(**filters).skip(skip).limit(limit).order_by('-status.trade_date')

        reservations = []
        for booking in bookings:
            current_status = booking.status[-1].reserve_status if booking.status else 'pending'

            reservations.append(BookingResponse(
                id=str(booking.id),
                room_id=str(booking.room.id),
                user_id=str(booking.user.id),
                start_time=booking.check_in,
                end_time=booking.check_out,
                total_price=booking.total,
                status=current_status
            ))

        return reservations

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener reservas: {str(e)}"
        )


@router.get("/{reservation_id}", response_model=ReservationDetails)
async def get_reservation_details(
        reservation_id: str,
        current_user: User = Depends(get_current_user)
        , status=None):
    """
    Obtiene los detalles completos de una reserva específica.
    """
    try:
        # Validar ObjectId
        if not ObjectId.is_valid(reservation_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de reserva inválido"
            )

        # Obtener reserva
        try:
            booking = Booking.objects.get(id=reservation_id)
        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reserva no encontrada"
            )

        # Verificar que la reserva pertenece al usuario actual
        if str(booking.user.id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para ver esta reserva"
            )

        # Construir respuesta detallada
        current_status = booking.status[-1].reserve_status if booking.status else 'pending'

        return ReservationDetails(
            id=str(booking.id),
            room_id=str(booking.room.id),
            room_name=booking.room.name,
            hotel_name=booking.room.hotel.name,
            user_id=str(booking.user.id),
            start_time=booking.check_in,
            end_time=booking.check_out,
            extra_services=[
                {
                    "name": service.name,
                    "price": service.price,
                    "description": service.description
                }
                for service in booking.extra_services
            ],
            total_price=booking.total,
            status=current_status,
            status_history=[
                {
                    "status": status.reserve_status,
                    "date": status.trade_date
                }
                for status in booking.status
            ],
            opinions=booking.opinions
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener detalles de la reserva: {str(e)}"
        )


@router.put("/{reservation_id}", response_model=BookingResponse)
async def update_reservation(
        reservation_id: str,
        reservation_update: BookingUpdate,
        current_user: User = Depends(get_current_user)
):
    """
    Actualiza una reserva existente (solo si está en estado 'pending').
    """
    try:
        # Validar ObjectId
        if not ObjectId.is_valid(reservation_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de reserva inválido"
            )

        # Obtener reserva
        try:
            booking = Booking.objects.get(id=reservation_id)
        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reserva no encontrada"
            )

        # Verificar permisos
        if str(booking.user.id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para modificar esta reserva"
            )

        # Verificar que se puede modificar
        current_status = booking.status[-1].reserve_status if booking.status else 'pending'
        if current_status not in ['pending']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se pueden modificar reservas en estado 'pending'"
            )

        # Actualizar campos permitidos
        updated = False

        if reservation_update.start_time:
            if reservation_update.start_time < datetime.now():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se puede cambiar a una fecha pasada"
                )
            booking.check_in = reservation_update.start_time
            updated = True

        if reservation_update.end_time:
            booking.check_out = reservation_update.end_time
            updated = True

        if reservation_update.additional_services is not None:
            # Actualizar servicios extras
            extra_services = []
            for service in reservation_update.additional_services:
                extra_service = ExtraService(
                    name=service.name,
                    price=service.price,
                    description=service.description
                )
                extra_services.append(extra_service)
            booking.extra_services = extra_services
            updated = True

        if updated:
            # Recalcular precio si hubo cambios
            nights = (booking.check_out.date() - booking.check_in.date()).days
            booking.total = calculate_total_price(booking.room.price, booking.extra_services, nights)

            # Agregar nuevo estado de actualización
            booking.status.append(ReserveStatus(
                reserve_status='pending',
                trade_date=datetime.now()
            ))

            booking.save()

        return BookingResponse(
            id=str(booking.id),
            room_id=str(booking.room.id),
            user_id=str(booking.user.id),
            start_time=booking.check_in,
            end_time=booking.check_out,
            total_price=booking.total,
            status=current_status
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar reserva: {str(e)}"
        )


@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_reservation(
        reservation_id: str,
        current_user: User = Depends(get_current_user)
):
    """
    Cancela una reserva (solo si está en estado 'pending' o 'confirmed').
    """
    try:
        # Validar ObjectId
        if not ObjectId.is_valid(reservation_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de reserva inválido"
            )

        # Obtener reserva
        try:
            booking = Booking.objects.get(id=reservation_id)
        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reserva no encontrada"
            )

        # Verificar permisos
        if str(booking.user.id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para cancelar esta reserva"
            )

        # Verificar que se puede cancelar
        if not can_cancel_reservation(booking):
            current_status = booking.status[-1].reserve_status if booking.status else 'pending'
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede cancelar una reserva en estado '{current_status}'"
            )

        # Cancelar reserva
        booking.status.append(ReserveStatus(
            reserve_status='cancelled',
            trade_date=datetime.now()
        ))
        booking.save()

        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cancelar reserva: {str(e)}"
        )


@router.post("/{reservation_id}/extras", response_model=BookingResponse)
async def add_extra_service(
        reservation_id: str,
        extra_service: ExtraServiceCreate,
        current_user: User = Depends(get_current_user)
):
    """
    Añade un servicio extra a una reserva existente.
    """
    try:
        # Validar ObjectId
        if not ObjectId.is_valid(reservation_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de reserva inválido"
            )

        # Obtener reserva
        try:
            booking = Booking.objects.get(id=reservation_id)
        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reserva no encontrada"
            )

        # Verificar permisos
        if str(booking.user.id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para modificar esta reserva"
            )

        # Verificar que se puede modificar
        current_status = booking.status[-1].reserve_status if booking.status else 'pending'
        if current_status not in ['pending', 'confirmed']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se pueden añadir servicios a reservas pendientes o confirmadas"
            )

        # Añadir servicio extra
        new_service = ExtraService(
            name=extra_service.name,
            price=extra_service.price,
            description=extra_service.description
        )

        booking.extra_services.append(new_service)

        # Recalcular precio total
        nights = (booking.check_out.date() - booking.check_in.date()).days
        booking.total = calculate_total_price(booking.room.price, booking.extra_services, nights)

        booking.save()

        return BookingResponse(
            id=str(booking.id),
            room_id=str(booking.room.id),
            user_id=str(booking.user.id),
            start_time=booking.check_in,
            end_time=booking.check_out,
            total_price=booking.total,
            status=current_status
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al añadir servicio extra: {str(e)}"
        )


@router.delete("/{reservation_id}/extras/{extra_index}", response_model=BookingResponse)
async def remove_extra_service(
        reservation_id: str,
        extra_index: int,
        current_user: User = Depends(get_current_user)
):
    """
    Elimina un servicio extra de una reserva por su índice.
    """
    try:
        # Validar ObjectId
        if not ObjectId.is_valid(reservation_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de reserva inválido"
            )

        # Obtener reserva
        try:
            booking = Booking.objects.get(id=reservation_id)
        except DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reserva no encontrada"
            )

        # Verificar permisos
        if str(booking.user.id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para modificar esta reserva"
            )

        # Verificar índice válido
        if extra_index < 0 or extra_index >= len(booking.extra_services):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Índice de servicio extra inválido"
            )

        # Verificar que se puede modificar
        current_status = booking.status[-1].reserve_status if booking.status else 'pending'
        if current_status not in ['pending', 'confirmed']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se pueden eliminar servicios de reservas pendientes o confirmadas"
            )

        # Eliminar servicio extra
        booking.extra_services.pop(extra_index)

        # Recalcular precio total
        nights = (booking.check_out.date() - booking.check_in.date()).days
        booking.total = calculate_total_price(booking.room.price, booking.extra_services, nights)

        booking.save()

        return BookingResponse(
            id=str(booking.id),
            room_id=str(booking.room.id),
            user_id=str(booking.user.id),
            start_time=booking.check_in,
            end_time=booking.check_out,
            total_price=booking.total,
            status=current_status
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar servicio extra: {str(e)}"
        )
