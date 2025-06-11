from datetime import datetime

from mongoengine import Document, ReferenceField, StringField, DateTimeField


class Payment(Document):
    reservation = ReferenceField("Booking", required=True)
    method = StringField(required=True, choices=['credit_card', 'cash', 'transfer'])
    status = StringField(required=True, choices=['pending', 'completed', 'failed'], default='pending')
    transaction_id = StringField(unique=True, required=True)
    date = DateTimeField(default=datetime.now)
    meta = {
        'collection': 'payments',
        'indexes': [
            'reservation',
            'status',
            'date',
        ]
    }
