from fastapi import APIRouter
from app.api.v1.endpoints import auth, chantiers, depenses, employes, materiels, rapports, documents, notifications

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(chantiers.router)
api_router.include_router(depenses.router)
api_router.include_router(employes.router)
api_router.include_router(materiels.router)
api_router.include_router(rapports.router)
api_router.include_router(documents.router)
api_router.include_router(notifications.router)
