from fastapi import APIRouter

from app.api.v1.endpoints import admin, ai, auth, customers, drivers, notifications, rides, tracking

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(customers.router)
api_router.include_router(drivers.router)
api_router.include_router(rides.router)
api_router.include_router(admin.router)
api_router.include_router(ai.router)
api_router.include_router(notifications.router)
api_router.include_router(tracking.router)
