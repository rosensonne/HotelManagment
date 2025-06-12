from mongoengine import (
    Document, IntField, StringField, FloatField,
    EmbeddedDocument, ListField, EmbeddedDocumentListField,
    BooleanField, EmbeddedDocumentField
)


class Amenity(EmbeddedDocument):
    name = StringField(required=True)
    icon = StringField(choices=[
        "wifi", "parking", "pool", "gym",
        "breakfast", "air_conditioning",
        "tv", "kitchen", "pet_friendly"
    ])


class Room(Document):
    number_room = IntField(unique=True, required=True)
    type = StringField(required=True, choices=[
        "standard", "deluxe", "suite",
        "family", "vip"
    ])
    price_per_night = FloatField(required=True)
    capacity = IntField(required=True, min_value=1)
    amenities = ListField(EmbeddedDocumentField(Amenity))
    availability = BooleanField(default=True)
    images = ListField(StringField())
    description = StringField()

    meta = {
        'collection': 'rooms',
        'indexes': [
            'number_room',
            'price_per_night',
            [("type", 1), ("availability", 1)],
            {
                'fields': ['type', 'price_per_night'],
                'name': 'idx_type_price'
            }
        ]
    }