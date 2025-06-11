from mongoengine import connect

from config import DATABASE_NAME, MONGO_URI


def connect_db():
    try:
        connect(db=DATABASE_NAME, host=MONGO_URI)
        print("Successfully connected to database")
    except:
        print("Failed to connect to database")