import uuid
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.schemas.monitoring import ServerMetricsResponse
from app.services.monitoring.cpu import parse_cpu_stat
from app.services.monitoring.memory import parse_meminfo
from app.services.monitoring.disk import parse_df_output
from app.services.monitoring.load import parse_loadavg
from app.services.monitoring.system_info import parse_system_info, parse_uptime_seconds
from app.services.monitoring.network import parse_network_interfaces
from app.services.monitoring.monitoring_service import MonitoringService
from app.models.server import Server
from app.models.server_credential import ServerCredential


# ---------------------------------------------------------
# 1. Unit Tests for Individual Metric Parsers
# ---------------------------------------------------------

def test_cpu_parser_valid_and_bounds():
    # Standard Linux /proc/stat
    sample_stat = """cpu  2255 34 2290 22625563 6290 127 456 0 0 0
cpu0 1132 17 1441 11311718 3675 127 438 0 0 0
cpu1 1123 17 849 11313845 2614 0 18 0 0 0
"""
    res = parse_cpu_stat(sample_stat, cpuinfo_content="2")
    assert res.error is None
    assert res.cores == 2
    assert res.usage_percent is not None
    assert 0.0 <= res.usage_percent <= 100.0

    # Zero CPU ticks
    zero_stat = "cpu 0 0 0 0 0 0 0 0 0 0"
    res_zero = parse_cpu_stat(zero_stat)
    assert res_zero.usage_percent == 0.0

    # 100% CPU ticks
    busy_stat = "cpu 1000 0 0 0 0 0 0 0 0 0"
    res_busy = parse_cpu_stat(busy_stat)
    assert res_busy.usage_percent == 100.0

    # Malformed stat
    res_malformed = parse_cpu_stat("not valid proc stat content")
    assert res_malformed.error is not None


def test_memory_parser_valid_and_malformed():
    sample_meminfo = """MemTotal:       16384000 kB
MemFree:         2048000 kB
MemAvailable:    8192000 kB
Buffers:          512000 kB
Cached:          4096000 kB
"""
    res = parse_meminfo(sample_meminfo)
    assert res.error is None
    assert res.total_bytes == 16384000 * 1024
    assert res.available_bytes == 8192000 * 1024
    assert res.free_bytes == 2048000 * 1024
    assert res.used_bytes == (16384000 - 8192000) * 1024
    assert res.usage_percent == 50.0

    # Missing MemTotal
    res_missing = parse_meminfo("MemFree: 2048000 kB\nBuffers: 100 kB")
    assert res_missing.error is not None

    # Malformed
    res_malformed = parse_meminfo("invalid meminfo text")
    assert res_malformed.error is not None


def test_disk_parser_valid_and_malformed():
    sample_df = """Filesystem     1K-blocks      Used Available Use% Mounted on
/dev/sda1      104857600  52428800  52428800  50% /
"""
    res = parse_df_output(sample_df, mount_point="/")
    assert res.error is None
    assert res.filesystem == "/dev/sda1"
    assert res.mount_point == "/"
    assert res.total_bytes == 104857600 * 1024
    assert res.used_bytes == 52428800 * 1024
    assert res.available_bytes == 52428800 * 1024
    assert res.usage_percent == 50.0

    # Malformed output
    res_empty = parse_df_output("")
    assert res_empty.error is not None

    # Header only
    res_hdr_only = parse_df_output("Filesystem 1K-blocks Used Available Use% Mounted on")
    assert res_hdr_only.error is not None


def test_load_parser_valid_and_malformed():
    sample_load = "0.82 0.64 0.51 1/450 12345"
    res = parse_loadavg(sample_load)
    assert res.error is None
    assert res.load_1m == 0.82
    assert res.load_5m == 0.64
    assert res.load_15m == 0.51

    # Malformed
    res_bad = parse_loadavg("bad load string")
    assert res_bad.error is not None


def test_uptime_and_system_info_parsers():
    sample_uptime = "1555200.45 3110400.90"
    uptime_sec = parse_uptime_seconds(sample_uptime)
    assert uptime_sec == 1555200

    assert parse_uptime_seconds("invalid") is None

    sys_info = parse_system_info(
        hostname_raw="prod-server-01",
        os_release_raw='NAME="Ubuntu"\nPRETTY_NAME="Ubuntu 24.04.1 LTS"\nVERSION="24.04"',
        kernel_raw="6.8.0-40-generic",
        arch_raw="x86_64",
    )
    assert sys_info.hostname == "prod-server-01"
    assert sys_info.operating_system == "Ubuntu 24.04.1 LTS"
    assert sys_info.kernel == "6.8.0-40-generic"
    assert sys_info.architecture == "x86_64"


def test_network_parser():
    # JSON output from ip -j addr
    sample_json = """[
        {"ifname": "lo", "addr_info": [{"family": "inet", "local": "127.0.0.1"}]},
        {"ifname": "eth0", "addr_info": [{"family": "inet", "local": "10.0.0.15"}]}
    ]"""
    net_json = parse_network_interfaces(sample_json)
    assert len(net_json.interfaces) == 1
    assert net_json.interfaces[0].name == "eth0"
    assert "10.0.0.15" in net_json.interfaces[0].addresses

    # Plain text ip addr fallback
    sample_text = """1: lo: <LOOPBACK,UP> mtu 65536
        inet 127.0.0.1/8 scope host lo
2: eth0: <BROADCAST,MULTICAST,UP> mtu 1500
        inet 192.168.1.100/24 brd 192.168.1.255 scope global eth0
"""
    net_text = parse_network_interfaces(sample_text)
    assert len(net_text.interfaces) == 1
    assert net_text.interfaces[0].name == "eth0"
    assert "192.168.1.100" in net_text.interfaces[0].addresses


# ---------------------------------------------------------
# 2. Integration Tests: Monitoring Endpoint & Authorization
# ---------------------------------------------------------

@pytest.fixture
def auth_headers_owner(client: TestClient) -> dict:
    email = f"mon_owner_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "name": "Mon Owner"})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_viewer(client: TestClient) -> dict:
    email = f"mon_viewer_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "name": "Mon Viewer"})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_server_metrics_success_online(client: TestClient, auth_headers_owner: dict):
    # 1. Create Workspace
    ws_res = client.post("/api/v1/workspaces", json={"name": "Metrics WS", "timezone": "Asia/Jakarta"}, headers=auth_headers_owner)
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]

    # 2. Create Environment
    env_res = client.post(f"/api/v1/workspaces/{ws_id}/environments", json={"name": "Prod", "key": "prod"}, headers=auth_headers_owner)
    env_id = env_res.json()["id"]

    # 3. Create Server with Credential
    srv_res = client.post(
        f"/api/v1/workspaces/{ws_id}/servers",
        json={
            "environment_id": env_id,
            "name": "Live Monitored Server",
            "hostname": "prod.app.internal",
            "ip_address": "10.0.0.50",
            "ssh_port": 22,
            "username": "ubuntu",
            "credential": {
                "auth_type": "PASSWORD",
                "username": "ubuntu",
                "password": "super-secret-password",
            },
        },
        headers=auth_headers_owner,
    )
    assert srv_res.status_code == 201
    srv_id = srv_res.json()["id"]

    # Mock ConnectionProvider.collect_raw_metrics
    mock_sections = {
        "CPU": "cpu  500 0 500 1000 0 0 0 0 0 0\ncpu0 500 0 500 1000 0 0 0 0 0 0",
        "CPUINFO": "4",
        "MEM": "MemTotal: 8388608 kB\nMemFree: 2097152 kB\nMemAvailable: 4194304 kB",
        "DISK": "Filesystem 1K-blocks Used Available Use% Mounted on\n/dev/sda1 104857600 52428800 52428800 50% /",
        "LOAD": "1.25 0.95 0.70 2/500 9876",
        "UPTIME": "864000.00 1728000.00",
        "SYSTEM": "prod-app-01\n---\nPRETTY_NAME=\"Ubuntu 24.04 LTS\"\n---\n6.8.0-generic\n---\nx86_64",
        "NET": '[{"ifname": "eth0", "addr_info": [{"family": "inet", "local": "10.0.0.50"}]}]',
    }

    mock_raw_res = {
        "success": True,
        "status": "ONLINE",
        "sections": mock_sections,
        "error": None,
    }

    with patch("app.services.connection_provider.SSHProvider.collect_raw_metrics", new_callable=AsyncMock) as mock_collect:
        mock_collect.return_value = mock_raw_res

        resp = client.get(f"/api/v1/workspaces/{ws_id}/servers/{srv_id}/metrics", headers=auth_headers_owner)
        assert resp.status_code == 200
        data = resp.json()

        assert data["server_id"] == srv_id
        assert data["status"] == "ONLINE"
        assert data["cpu"]["usage_percent"] == 50.0
        assert data["cpu"]["cores"] == 4
        assert data["memory"]["total_bytes"] == 8388608 * 1024
        assert data["memory"]["usage_percent"] == 50.0
        assert data["disk"]["usage_percent"] == 50.0
        assert data["load"]["load_1m"] == 1.25
        assert data["uptime_seconds"] == 864000
        assert data["system"]["hostname"] == "prod-app-01"
        assert data["system"]["operating_system"] == "Ubuntu 24.04 LTS"
        assert len(data["network"]["interfaces"]) == 1


@pytest.mark.asyncio
async def test_get_server_metrics_offline_and_partial_failure(client: TestClient, auth_headers_owner: dict):
    # Setup WS, Env, Server
    ws_res = client.post("/api/v1/workspaces", json={"name": "Offline WS"}, headers=auth_headers_owner)
    ws_id = ws_res.json()["id"]
    env_res = client.post(f"/api/v1/workspaces/{ws_id}/environments", json={"name": "Staging", "key": "staging"}, headers=auth_headers_owner)
    env_id = env_res.json()["id"]
    srv_res = client.post(
        f"/api/v1/workspaces/{ws_id}/servers",
        json={"environment_id": env_id, "name": "Offline Srv", "ip_address": "192.168.1.99"},
        headers=auth_headers_owner,
    )
    srv_id = srv_res.json()["id"]

    # 1. Total Offline Case
    with patch("app.services.connection_provider.SSHProvider.collect_raw_metrics", new_callable=AsyncMock) as mock_collect:
        mock_collect.return_value = {
            "success": False,
            "status": "OFFLINE",
            "sections": {},
            "error": "Connection timed out (5s).",
        }

        resp = client.get(f"/api/v1/workspaces/{ws_id}/servers/{srv_id}/metrics", headers=auth_headers_owner)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "OFFLINE"
        assert "timed out" in data["error"]
        assert data["cpu"] is None

    # 2. Partial Metric Failure (Disk fails, but CPU/RAM/Load work)
    partial_sections = {
        "CPU": "cpu  100 0 100 800 0 0 0 0 0 0",
        "CPUINFO": "2",
        "MEM": "MemTotal: 4194304 kB\nMemAvailable: 2097152 kB",
        "DISK": "malformed df output",
        "LOAD": "0.10 0.20 0.30",
        "UPTIME": "3600.0",
        "SYSTEM": "partial-srv\n---\nLinux",
    }

    with patch("app.services.connection_provider.SSHProvider.collect_raw_metrics", new_callable=AsyncMock) as mock_collect:
        mock_collect.return_value = {
            "success": True,
            "status": "ONLINE",
            "sections": partial_sections,
            "error": None,
        }

        resp = client.get(f"/api/v1/workspaces/{ws_id}/servers/{srv_id}/metrics", headers=auth_headers_owner)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ONLINE"
        assert data["cpu"]["usage_percent"] == 20.0
        assert data["disk"]["error"] is not None  # Specific metric error captured
        assert data["load"]["load_1m"] == 0.10


@pytest.mark.asyncio
async def test_metrics_authorization_and_cross_workspace_rejected(
    client: TestClient,
    auth_headers_owner: dict,
    auth_headers_viewer: dict,
):
    # WS A (Owned by Owner)
    ws_a = client.post("/api/v1/workspaces", json={"name": "WS A"}, headers=auth_headers_owner).json()["id"]
    env_a = client.post(f"/api/v1/workspaces/{ws_a}/environments", json={"name": "A", "key": "a"}, headers=auth_headers_owner).json()["id"]
    srv_a = client.post(f"/api/v1/workspaces/{ws_a}/servers", json={"environment_id": env_a, "name": "Server A", "ip_address": "10.0.0.1"}, headers=auth_headers_owner).json()["id"]

    # WS B (Owned by Viewer User)
    ws_b = client.post("/api/v1/workspaces", json={"name": "WS B"}, headers=auth_headers_viewer).json()["id"]

    # 1. Non-member access to WS A Server -> 404 Not Found (IDOR Shield)
    resp_forbidden = client.get(f"/api/v1/workspaces/{ws_a}/servers/{srv_a}/metrics", headers=auth_headers_viewer)
    assert resp_forbidden.status_code == 404

    # 2. Cross-workspace ID mismatch (Querying Server A under Workspace B) -> 404 Not Found
    resp_cross = client.get(f"/api/v1/workspaces/{ws_b}/servers/{srv_a}/metrics", headers=auth_headers_viewer)
    assert resp_cross.status_code == 404
