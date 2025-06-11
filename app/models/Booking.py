from datetime import datetime

from mongoengine import Document, EmbeddedDocument, StringField, FloatField, ReferenceField, DateTimeField, ListField, \
    EmbeddedDocumentField


class ExtraService(EmbeddedDocument):
    name = StringField(required=True)
    price = FloatField(required=True, min_value=0.0)
    description = StringField()


class ReserveStatus(EmbeddedDocument):
    reserve_status = StringField(choices=['pending', 'confirmed', 'cancelled', 'completed'], default='pending')
    trade_date = DateTimeField(default=datetime.now)


class Booking(Document):
    room = ReferenceField("Room", required=True)
    user = ReferenceField("User", required=True)
    check_in = DateTimeField(required=True)
    check_out = DateTimeField(required=True)
    extra_services = ListField(EmbeddedDocumentField(ExtraService), default=list)
    total = FloatField(required=True)
    status = ListField(EmbeddedDocumentField(ReserveStatus), default=list)
    opinions = StringField()
    meta = {
        'collection': 'bookings',
        'indexes': [
            'room',
            'user',('check_in', 'check_out'),
            'status.reserve_status',
        ]
    }
