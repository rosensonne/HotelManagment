from fastapi import FastAPI


from app.database import connect_db
from app.routers import rooms, users, auth

app = FastAPI(title="Hotel Management API")



connect_db()

app.include_router(rooms.router)
app.include_router(auth.router)
app.include_router(users.router)

print("Hotel Management API is running...")