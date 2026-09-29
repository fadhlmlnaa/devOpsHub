from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.workspaces import router as workspaces_router
from app.api.v1.environments import router as environments_router
from app.api.v1.servers import router as servers_router
from app.api.v1.services import router as services_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(workspaces_router)
api_v1_router.include_router(environments_router)
api_v1_router.include_router(servers_router)
api_v1_router.include_router(services_router)
