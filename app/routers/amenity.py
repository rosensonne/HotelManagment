# app/routers/amenity.py
from typing import List
from fastapi import APIRouter
from app.schemas.amenity_schema import AmenityBase

router = APIRouter(prefix="/amenities", tags=["amenities"])


@router.get("/", response_model=List[AmenityBase])
def get_all_amenities():
    """
    Obtener lista de todas las amenidades disponibles
    con sus íconos correspondientes
    """

    # Lista predefinida de amenidades disponibles
    amenities = [
        {"name": "WiFi Gratis", "icon": "wifi"},
        {"name": "Estacionamiento", "icon": "parking"},
        {"name": "Piscina", "icon": "pool"},
        {"name": "Gimnasio", "icon": "gym"},
        {"name": "Desayuno Incluido", "icon": "breakfast"},
        {"name": "Aire Acondicionado", "icon": "air_conditioning"},
        {"name": "TV por Cable", "icon": "tv"},
        {"name": "Cocina Equipada", "icon": "kitchen"},
        {"name": "Pet Friendly", "icon": "pet_friendly"}
    ]

    return amenities


@router.get("/icons")
def get_available_icons():
    """Obtener lista de íconos disponibles para amenidades"""

    icons = [
        "wifi", "parking", "pool", "gym",
        "breakfast", "air_conditioning",
        "tv", "kitchen", "pet_friendly"
    ]

    return {"available_icons": icons}