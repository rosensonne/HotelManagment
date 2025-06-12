# app/utils/room_utils.py
from datetime import datetime
from typing import List
from bson import ObjectId
from mongoengine import DoesNotExist

from app.models.Room import Room


def validate_room_availability(room_id: str, check_in: datetime, check_out: datetime) -> bool:
    """
    Verifica si una habitación está disponible en las fechas especificadas

    Args:
        room_id: ID de la habitación
        check_in: Fecha de entrada
        check_out: Fecha de salida

    Returns:
        bool: True si está disponible, False si no
    """

    try:
        room_oid = ObjectId(room_id)
        room = Room.objects.get(id=room_oid)

        # Verificar disponibilidad básica
        if not room.availability:
            return False

        # TODO: Cuando implementes el módulo de Reservations,
        # verificar solapamientos con reservas existentes:

        # from app.models.Reservation import Reservation
        #
        # overlapping_reservations = Reservation.objects.filter(
        #     room=room,
        #     status__in=["confirmed", "checked_in"],
        #     check_out__gt=check_in,
        #     check_in__lt=check_out
        # )
        #
        # return len(overlapping_reservations) == 0

        # Por ahora, solo verificamos availability básica
        return True

    except DoesNotExist:
        return False


def get_available_room_types() -> List[str]:
    """Obtener tipos de habitación disponibles"""
    return ["standard", "deluxe", "suite", "family", "vip"]


def calculate_room_price(room_id: str, nights: int) -> float:
    """
    Calcular precio total de una habitación por número de noches

    Args:
        room_id: ID de la habitación
        nights: Número de noches

    Returns:
        float: Precio total
    """

    try:
        room_oid = ObjectId(room_id)
        room = Room.objects.get(id=room_oid)
        return room.price_per_night * nights

    except DoesNotExist:
        raise ValueError(f"Room with ID {room_id} not found")


def search_rooms_by_criteria(
        room_type: str = None,
        min_capacity: int = None,
        max_price: float = None,
        amenities: List[str] = None
) -> List[Room]:
    """
    Buscar habitaciones por criterios específicos

    Args:
        room_type: Tipo de habitación
        min_capacity: Capacidad mínima
        max_price: Precio máximo por noche
        amenities: Lista de amenidades requeridas

    Returns:
        List[Room]: Lista de habitaciones que cumplen los criterios
    """

    filters = {'availability': True}

    if room_type:
        filters['type'] = room_type
    if min_capacity:
        filters['capacity__gte'] = min_capacity
    if max_price:
        filters['price_per_night__lte'] = max_price

    rooms = Room.objects.filter(**filters)

    # Filtrar por amenidades si se especifican
    if amenities:
        filtered_rooms = []
        for room in rooms:
            room_amenity_names = [amenity.name.lower() for amenity in room.amenities]
            if all(amenity.lower() in room_amenity_names for amenity in amenities):
                filtered_rooms.append(room)
        return filtered_rooms

    return list(rooms)