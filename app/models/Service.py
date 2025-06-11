from mongoengine import FloatField, Document, StringField, EmbeddedDocument, EmbeddedDocumentField, ListField, \
    BooleanField


class HourService(EmbeddedDocument):
    day = StringField(choices=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    start_time = StringField(regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    end_time = StringField()

class Service(Document):
    name = StringField(required=True, unique=True)
    description = StringField()
    price = FloatField(required=True)
    category = StringField(choices=['spa', 'restaurante', 'gym', 'pool', 'other'])
    schedule = ListField(EmbeddedDocumentField(HourService))
    availability  = BooleanField(default=True)
    meta = {
        'collection': 'services',
        'indexes': ['name', 'category', 'availability ']
    }