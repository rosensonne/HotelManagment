# app/routers/room.py - Versión completa
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from mongoengine import DoesNotExist

from app.models.Room import Room
from app.schemas.room_schema import RoomResponse, RoomCreate, RoomUpdate

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("/create", response_model=RoomResponse)
def create_room(room: RoomCreate):
    room_data = room.dict()
    new_room = Room(**room_data).save()

    # Convertir a dict y cambiar _id por id
    room_dict = new_room.to_mongo().to_dict()
    room_dict['id'] = str(room_dict.pop('_id'))

    return room_dict


@router.get("/", response_model=List[RoomResponse])
def get_available_rooms(
        check_in: Optional[datetime] = Query(None, description="Fecha de entrada (YYYY-MM-DD)"),
        check_out: Optional[datetime] = Query(None, description="Fecha de salida (YYYY-MM-DD)"),
        room_type: Optional[str] = Query(None, description="Tipo de habitación"),
        min_capacity: Optional[int] = Query(None, ge=1, description="Capacidad mínima"),
        max_price: Optional[float] = Query(None, ge=0, description="Precio máximo por noche")
):

    #Filtros básicos
    filters = {'availability': True}  # Solo habitaciones disponibles

    if room_type:
        filters['type'] = room_type
    if min_capacity:
        filters['capacity__gte'] = min_capacity
    if max_price:
        filters['price_per_night__lte'] = max_price

    rooms = Room.objects.filter(**filters)

    # Si se proporcionan fechas, verificar disponibilidad
    if check_in and check_out:
        if check_in >= check_out:
            raise HTTPException(
                status_code=400,
                detail="Check-in date must be before check-out date"
            )

        # TODO: Aquí necesitarías verificar contra las reservas existentes
        # Por ahora, solo filtramos por availability=True
        # Cuando implementes Reservations, añadir lógica de verificación de fechas
        available_rooms = []
        for room in rooms:
            # Placeholder para verificación de disponibilidad por fechas
            # if validate_room_availability(str(room.id), check_in, check_out):
            available_rooms.append(room)
        rooms = available_rooms

    # Convertir a formato de respuesta
    rooms_list = []
    for room in rooms:
        room_dict = room.to_mongo().to_dict()
        room_dict['id'] = str(room_dict.pop('_id'))
        rooms_list.append(room_dict)

    return rooms_list


@router.get("/{room_id}", response_model=RoomResponse)
def get_room_details(room_id: str):
    """Obtener información completa de una habitación específica"""

    try:
        room_oid = ObjectId(room_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    try:
        room = Room.objects.get(id=room_oid)

        # Convertir a dict y cambiar _id por id
        room_dict = room.to_mongo().to_dict()
        room_dict['id'] = str(room_dict.pop('_id'))

        return room_dict

    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Room not found")


@router.put("/{room_id}", response_model=RoomResponse)
def update_room(room_id: str, room_update: RoomUpdate):
    """Actualizar información de una habitación"""

    try:
        room_oid = ObjectId(room_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    try:
        room = Room.objects.get(id=room_oid)

        # Actualizar campos
        update_data = room_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(room, field, value)

        room.save()

        # Convertir a dict y cambiar _id por id
        room_dict = room.to_mongo().to_dict()
        room_dict['id'] = str(room_dict.pop('_id'))

        return room_dict

    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Room not found")


@router.delete("/{room_id}")
def delete_room(room_id: str):
    """Eliminar una habitación"""

    try:
        room_oid = ObjectId(room_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    try:
        room = Room.objects.get(id=room_oid)
        room.delete()
        return {"message": "Room deleted successfully"}

    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Room not found")