from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.workspaces import router as workspaces_router
from app.api.v1.environments import router as environments_router
from app.api.v1.servers import router as servers_router
from app.api.v1.services import router as services_router
from app.api.v1.logs import router as logs_router
from app.api.v1.docker import router as docker_router
from app.api.v1.deployments import router as deployments_router
from app.api.v1.backups import router as backups_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.audit_logs import router as audit_logs_router
from app.api.v1.agents import router as agents_router
from app.api.v1.terminal import router as terminal_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(workspaces_router)
api_v1_router.include_router(environments_router)
api_v1_router.include_router(servers_router)
api_v1_router.include_router(services_router)
api_v1_router.include_router(logs_router)
api_v1_router.include_router(docker_router)
api_v1_router.include_router(deployments_router)
api_v1_router.include_router(backups_router)
api_v1_router.include_router(alerts_router)
api_v1_router.include_router(audit_logs_router)
api_v1_router.include_router(agents_router)
api_v1_router.include_router(terminal_router)




