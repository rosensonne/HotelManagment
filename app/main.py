from fastapi import FastAPI


from app.database import connect_db
from app.routers import rooms, users, auth, hotel, amenity

app = FastAPI(title="Hotel Management API")


connect_db()

app.include_router(rooms.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(hotel.router)
app.include_router(amenity.router)

print("Hotel Management API is running...")