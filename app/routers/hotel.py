from typing import List, Optional
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from mongoengine import DoesNotExist

from app.models.Hotel import Hotel
from app.schemas.hotel_schema import HotelResponse, HotelCreate, HotelListResponse

router = APIRouter(prefix="/hotels", tags=["hotels"])


@router.post("/create", response_model=HotelResponse)
def create_hotel(hotel: HotelCreate):
    hotel_data = hotel.dict()
    new_hotel = Hotel(**hotel_data).save()

    # Convertir a dict y cambiar _id por id
    hotel_dict = new_hotel.to_mongo().to_dict()
    hotel_dict['id'] = str(hotel_dict.pop('_id'))

    return hotel_dict


@router.get("/", response_model=List[HotelListResponse])
def get_all_hotels(
        city: Optional[str] = Query(None, description="Filtrar por ciudad"),
        country: Optional[str] = Query(None, description="Filtrar por país"),
        min_rating: Optional[float] = Query(None, ge=0.0, le=5.0, description="Rating mínimo")
):
    #Filtros dinamicos
    filters = {}
    if city:
        filters['address__city__icontains'] = city
    if country:
        filters['address__country__icontains'] = country
    if min_rating is not None:
        filters['rating__gte'] = min_rating

    hotels = Hotel.objects.filter(**filters)

    # Convertir a formato de respuesta
    hotels_list = []
    for hotel in hotels:
        hotel_dict = hotel.to_mongo().to_dict()
        hotel_dict['id'] = str(hotel_dict.pop('_id'))
        hotels_list.append(hotel_dict)

    return hotels_list


@router.get("/{hotel_id}", response_model=HotelResponse)
def get_hotel(hotel_id: str):

    try:
        hotel_oid = ObjectId(hotel_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    try:
        hotel = Hotel.objects.get(id=hotel_oid)

        # Convertir a dict y cambiar _id por id
        hotel_dict = hotel.to_mongo().to_dict()
        hotel_dict['id'] = str(hotel_dict.pop('_id'))

        # Convertir room references a strings
        if 'rooms' in hotel_dict:
            hotel_dict['rooms'] = [str(room_id) for room_id in hotel_dict['rooms']]

        return hotel_dict

    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Hotel not found")