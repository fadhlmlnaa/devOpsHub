from agent.operations.monitoring import (
    execute_get_system_metrics,
    execute_get_server_info,
)
from agent.operations.systemd import (
    execute_get_service_status,
    execute_start_service,
    execute_stop_service,
    execute_restart_service,
    execute_reload_service,
)
from agent.operations.docker import (
    execute_get_docker_info,
    execute_list_docker_containers,
    execute_get_docker_container,
    execute_start_docker_container,
    execute_stop_docker_container,
    execute_restart_docker_container,
    execute_get_docker_logs,
)
from agent.operations.deployment import execute_deployment
from agent.operations.backup import execute_backup
from agent.operations.logs import execute_get_service_logs

OPERATIONS_REGISTRY = {
    "GET_SYSTEM_METRICS": execute_get_system_metrics,
    "GET_SERVER_INFO": execute_get_server_info,
    "GET_SERVICE_STATUS": execute_get_service_status,
    "START_SERVICE": execute_start_service,
    "STOP_SERVICE": execute_stop_service,
    "RESTART_SERVICE": execute_restart_service,
    "RELOAD_SERVICE": execute_reload_service,
    "GET_SERVICE_LOGS": execute_get_service_logs,
    "GET_DOCKER_INFO": execute_get_docker_info,
    "LIST_DOCKER_CONTAINERS": execute_list_docker_containers,
    "GET_DOCKER_CONTAINER": execute_get_docker_container,
    "START_DOCKER_CONTAINER": execute_start_docker_container,
    "STOP_DOCKER_CONTAINER": execute_stop_docker_container,
    "RESTART_DOCKER_CONTAINER": execute_restart_docker_container,
    "GET_DOCKER_LOGS": execute_get_docker_logs,
    "DEPLOY": execute_deployment,
    "BACKUP": execute_backup,
}
