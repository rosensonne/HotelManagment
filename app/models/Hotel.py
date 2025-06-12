
from mongoengine import (
    Document, StringField, FloatField, ListField,
    EmbeddedDocumentField, ReferenceField, EmbeddedDocument
)
from app.models.Room import Room, Amenity


class Address(EmbeddedDocument):
    street = StringField(required=True)
    city = StringField(required=True)
    state = StringField(required=True)
    country = StringField(required=True)
    postal_code = StringField(required=True)


class Hotel(Document):
    name = StringField(required=True, max_length=200)
    description = StringField()
    address = EmbeddedDocumentField(Address, required=True)
    phone = StringField()
    email = StringField()
    website = StringField()
    rating = FloatField(min_value=0.0, max_value=5.0, default=0.0)
    images = ListField(StringField())
    amenities = ListField(EmbeddedDocumentField(Amenity))
    rooms = ListField(ReferenceField(Room))  # Referencias a habitaciones

    meta = {
        'collection': 'hotels',
        'indexes': [
            'name',
            'address.city',
            'address.country',
            'rating',
            {
                'fields': ['address.city', 'rating'],
                'name': 'idx_city_rating'
            }
        ]
    }