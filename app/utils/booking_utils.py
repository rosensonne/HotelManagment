from datetime import datetime, timedelta
from typing import List, Optional
from mongoengine import Q

from app.models.Booking import Booking, ExtraService
from app.models.Room import Room


def validate_room_availability(room_id: str, check_in: datetime, check_out: datetime) -> bool:
    """
    Verifica si una habitación está disponible en las fechas especificadas.

    Args:
        room_id: ID de la habitación
        check_in: Fecha de entrada
        check_out: Fecha de salida

    Returns:
        bool: True si está disponible, False si no
    """
    try:
        # Buscar reservas que se solapen con las fechas solicitadas
        overlapping_reservations = Booking.objects(
            room=room_id,
            # Excluir reservas canceladas
            status__not__match={"reserve_status": "cancelled"}
        ).filter(
            # Condiciones de solapamiento:
            # 1. La reserva existente empieza antes de que termine la nueva
            # 2. La reserva existente termina después de que empiece la nueva
            Q(check_in__lt=check_out) & Q(check_out__gt=check_in)
        )

        # Si no hay reservas que se solapen, la habitación está disponible
        return overlapping_reservations.count() == 0

    except Exception as e:
        print(f"Error checking room availability: {e}")
        return False


def calculate_total_price(room_price: float, extra_services: List[ExtraService], nights: int) -> float:
    """
    Calcula el precio total de una reserva.

    Args:
        room_price: Precio por noche de la habitación
        extra_services: Lista de servicios extras
        nights: Número de noches

    Returns:
        float: Precio total
    """
    try:
        # Precio base (habitación * noches)
        base_price = room_price * nights

        # Sumar servicios extras
        extras_total = sum(service.price for service in extra_services)

        return base_price + extras_total

    except Exception as e:
        print(f"Error calculating total price: {e}")
        return 0.0


def can_cancel_reservation(booking: Booking) -> bool:
    """
    Determina si una reserva puede ser cancelada.

    Args:
        booking: Objeto de reserva

    Returns:
        bool: True si se puede cancelar, False si no
    """
    try:
        # Obtener el último estado
        if not booking.status:
            return True  # Si no hay estado, asumimos que se puede cancelar

        current_status = booking.status[-1].reserve_status

        # Solo se pueden cancelar reservas pendientes o confirmadas
        if current_status not in ['pending', 'confirmed']:
            return False

        # Verificar si falta más de 24 horas para el check-in
        hours_until_checkin = (booking.check_in - datetime.now()).total_seconds() / 3600

        return hours_until_checkin > 24

    except Exception as e:
        print(f"Error checking if reservation can be cancelled: {e}")
        return False


def get_conflicting_reservations(room_id: str, check_in: datetime, check_out: datetime) -> List[str]:
    """
    Obtiene las reservas que entran en conflicto con las fechas especificadas.

    Args:
        room_id: ID de la habitación
        check_in: Fecha de entrada
        check_out: Fecha de salida

    Returns:
        List[str]: Lista de IDs de reservas en conflicto
    """
    try:
        conflicting_bookings = Booking.objects(
            room=room_id,
            status__not__match={"reserve_status": "cancelled"}
        ).filter(
            Q(check_in__lt=check_out) & Q(check_out__gt=check_in)
        )

        return [str(booking.id) for booking in conflicting_bookings]

    except Exception as e:
        print(f"Error getting conflicting reservations: {e}")
        return []


def calculate_occupancy_rate(room_id: str, start_date: datetime, end_date: datetime) -> float:
    """
    Calcula la tasa de ocupación de una habitación en un período específico.

    Args:
        room_id: ID de la habitación
        start_date: Fecha de inicio del período
        end_date: Fecha de fin del período

    Returns:
        float: Tasa de ocupación (0.0 - 1.0)
    """
    try:
        total_days = (end_date.date() - start_date.date()).days
        if total_days <= 0:
            return 0.0

        # Obtener todas las reservas confirmadas en el período
        bookings = Booking.objects(
            room=room_id,
            status__match={"reserve_status": "confirmed"}
        ).filter(
            Q(check_in__lt=end_date) & Q(check_out__gt=start_date)
        )

        occupied_days = 0
        for booking in bookings:
            # Calcular intersección entre la reserva y el período consultado
            booking_start = max(booking.check_in.date(), start_date.date())
            booking_end = min(booking.check_out.date(), end_date.date())

            if booking_start < booking_end:
                occupied_days += (booking_end - booking_start).days

        return min(occupied_days / total_days, 1.0)

    except Exception as e:
        print(f"Error calculating occupancy rate: {e}")
        return 0.0


def get_available_rooms(check_in: datetime, check_out: datetime, hotel_id: Optional[str] = None) -> List[str]:
    """
    Obtiene lista de habitaciones disponibles en las fechas especificadas.

    Args:
        check_in: Fecha de entrada
        check_out: Fecha de salida
        hotel_id: ID del hotel (opcional)

    Returns:
        List[str]: Lista de IDs de habitaciones disponibles
    """
    try:
        # Obtener todas las habitaciones (filtrar por hotel si se especifica)
        room_filters = {}
        if hotel_id:
            room_filters['hotel'] = hotel_id

        all_rooms = Room.objects(**room_filters)

        # Filtrar habitaciones disponibles
        available_rooms = []
        for room in all_rooms:
            if validate_room_availability(str(room.id), check_in, check_out):
                available_rooms.append(str(room.id))

        return available_rooms

    except Exception as e:
        print(f"Error getting available rooms: {e}")
        return []


def update_reservation_status(booking_id: str, new_status: str, reason: Optional[str] = None) -> bool:
    """
    Actualiza el estado de una reserva agregando un nuevo registro al historial.

    Args:
        booking_id: ID de la reserva
        new_status: Nuevo estado
        reason: Razón del cambio (opcional)

    Returns:
        bool: True si se actualizó correctamente, False si no
    """
    try:
        from app.models.Booking import ReserveStatus

        # Obtener la reserva
        booking = Booking.objects.get(id=booking_id)

        # Validar transición de estado
        current_status = booking.status[-1].reserve_status if booking.status else 'pending'

        valid_transitions = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['completed', 'cancelled'],
            'cancelled': [],  # No se puede cambiar desde cancelado
            'completed': []  # No se puede cambiar desde completado
        }

        if new_status not in valid_transitions.get(current_status, []):
            print(f"Invalid status transition from {current_status} to {new_status}")
            return False

        # Agregar nuevo estado al historial
        new_status_record = ReserveStatus(
            reserve_status=new_status,
            trade_date=datetime.now()
        )

        booking.status.append(new_status_record)
        booking.save()

        return True

    except Exception as e:
        print(f"Error updating reservation status: {e}")
        return False


def get_reservation_statistics(user_id: Optional[str] = None, hotel_id: Optional[str] = None) -> dict:
    """
    Obtiene estadísticas de reservas.

    Args:
        user_id: ID del usuario (opcional, para estadísticas específicas)
        hotel_id: ID del hotel (opcional, para estadísticas específicas)

    Returns:
        dict: Diccionario con estadísticas
    """
    try:
        # Construir filtros
        filters = {}
        if user_id:
            filters['user'] = user_id
        if hotel_id:
            filters['room__hotel'] = hotel_id

        # Obtener todas las reservas que coincidan con los filtros
        all_bookings = Booking.objects(**filters)

        # Contar por estado
        status_counts = {
            'pending': 0,
            'confirmed': 0,
            'cancelled': 0,
            'completed': 0
        }

        total_revenue = 0.0

        for booking in all_bookings:
            current_status = booking.status[-1].reserve_status if booking.status else 'pending'
            status_counts[current_status] += 1

            # Solo contar ingresos de reservas confirmadas y completadas
            if current_status in ['confirmed', 'completed']:
                total_revenue += booking.total

        return {
            'total_reservations': len(all_bookings),
            'pending_reservations': status_counts['pending'],
            'confirmed_reservations': status_counts['confirmed'],
            'cancelled_reservations': status_counts['cancelled'],
            'completed_reservations': status_counts['completed'],
            'total_revenue': total_revenue,
            'average_reservation_value': total_revenue / max(status_counts['confirmed'] + status_counts['completed'], 1)
        }

    except Exception as e:
        print(f"Error getting reservation statistics: {e}")
        return {}


def check_and_update_expired_reservations():
    """
    Verifica y actualiza reservas que han expirado.
    Esta función debería ejecutarse periódicamente (ej: cron job).
    """
    try:
        from app.models.Booking import ReserveStatus

        now = datetime.now()

        # Buscar reservas pendientes que deberían haber comenzado hace más de 24 horas
        expired_pending = Booking.objects(
            status__match={"reserve_status": "pending"},
            check_in__lt=now - timedelta(hours=24)
        )

        for booking in expired_pending:
            # Cancelar automáticamente
            booking.status.append(ReserveStatus(
                reserve_status='cancelled',
                trade_date=now
            ))
            booking.save()
            print(f"Auto-cancelled expired reservation: {booking.id}")

        # Buscar reservas confirmadas que ya terminaron
        completed_reservations = Booking.objects(
            status__match={"reserve_status": "confirmed"},
            check_out__lt=now
        )

        for booking in completed_reservations:
            # Marcar como completada
            booking.status.append(ReserveStatus(
                reserve_status='completed',
                trade_date=now
            ))
            booking.save()
            print(f"Auto-completed reservation: {booking.id}")

        return True

    except Exception as e:
        print(f"Error updating expired reservations: {e}")
        return False


def validate_reservation_dates(check_in: datetime, check_out: datetime) -> tuple[bool, str]:
    """
    Valida que las fechas de reserva sean correctas.

    Args:
        check_in: Fecha de entrada
        check_out: Fecha de salida

    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        now = datetime.now()

        # Validar que check_in no sea en el pasado
        if check_in < now:
            return False, "La fecha de entrada no puede ser en el pasado"

        # Validar que check_out sea después de check_in
        if check_out <= check_in:
            return False, "La fecha de salida debe ser posterior a la fecha de entrada"

        # Validar que la estancia no sea demasiado larga (ej: máximo 30 días)
        max_stay_days = 30
        stay_duration = (check_out.date() - check_in.date()).days
        if stay_duration > max_stay_days:
            return False, f"La estancia no puede ser mayor a {max_stay_days} días"

        # Validar que la reserva no sea demasiado anticipada (ej: máximo 1 año)
        max_advance_days = 365
        advance_days = (check_in.date() - now.date()).days
        if advance_days > max_advance_days:
            return False, f"No se pueden hacer reservas con más de {max_advance_days} días de anticipación"

        return True, ""

    except Exception as e:
        return False, f"Error validating dates: {str(e)}"


def calculate_cancellation_fee(booking: Booking) -> float:
    """
    Calcula la tarifa de cancelación basada en cuánto tiempo falta para el check-in.

    Args:
        booking: Objeto de reserva

    Returns:
        float: Monto de la tarifa de cancelación
    """
    try:
        now = datetime.now()
        hours_until_checkin = (booking.check_in - now).total_seconds() / 3600

        # Política de cancelación:
        # - Más de 48 horas: sin cargo
        # - 24-48 horas: 25% del total
        # - Menos de 24 horas: 50% del total

        if hours_until_checkin > 48:
            return 0.0
        elif hours_until_checkin > 24:
            return booking.total * 0.25
        else:
            return booking.total * 0.50

    except Exception as e:
        print(f"Error calculating cancellation fee: {e}")
        return 0.0