from bson import ObjectId
from fastapi import APIRouter, HTTPException
from mongoengine import DoesNotExist  # Importar la excepción

from app.models.Room import Room
from app.schemas.room_schema import RoomResponse, RoomCreate

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("/create", response_model=RoomResponse)
def create_room(room: RoomCreate):
    # Convertir el dict del schema al formato del modelo
    room_data = room.dict()
    new_room = Room(**room_data).save()
    return new_room


@router.get("/{room_id}", response_model=RoomResponse)
def get_room(room_id: str):
    print(f"Received Room ID: {room_id}")

    try:
        room_oid = ObjectId(room_id)
    except Exception as e:
        print(f"Invalid ObjectId format: {e}")
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    try:
        room = Room.objects.get(id=room_oid)
        print(f"Room found: {room}")

        # Convertir a dict y cambiar _id por id
        room_dict = room.to_mongo().to_dict()
        room_dict['id'] = str(room_dict.pop('_id'))  # Cambiar _id por id

        return room_dict

    except DoesNotExist:
        print(f"Room with ID {room_id} not found!")
        raise HTTPException(status_code=404, detail="Room not found")