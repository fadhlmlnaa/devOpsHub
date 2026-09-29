#!/usr/bin/env python3
"""
DevOpsHub Production Readiness Automated Smoke Test Script
Executes end-to-end sanity tests against target API URL using standard library.
"""
import sys
import uuid
import json
import urllib.request
import urllib.error

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
API_URL = f"{BASE_URL.rstrip('/')}/api/v1"


def print_step(name: str):
    print(f"\n[TEST] {name}...")


def http_request(method: str, url: str, data: dict = None, headers: dict = None):
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)

    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status_code = resp.status
            resp_headers = dict(resp.headers)
            content = resp.read().decode("utf-8")
            parsed = json.loads(content) if content else {}
            return status_code, parsed, resp_headers
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        parsed = json.loads(content) if content else {}
        return e.code, parsed, dict(e.headers)
    except Exception as e:
        print(f" [ERROR] Request failed: {e}")
        sys.exit(1)


def assert_status(status_code: int, expected: int, action: str):
    if status_code != expected:
        print(f" [FAIL] {action} failed. Expected {expected}, got {status_code}")
        sys.exit(1)
    print(f" [PASS] {action} (HTTP {status_code})")


def main():
    print("==========================================================")
    print(f" DevOpsHub Production Smoke Test Target: {API_URL}")
    print("==========================================================")

    # 1. Liveness Probe
    print_step("1. Checking Liveness Probe (/health/live)")
    s, data, hdrs = http_request("GET", f"{API_URL}/health/live")
    assert_status(s, 200, "Liveness Probe")
    assert "X-Request-ID" in hdrs or "x-request-id" in hdrs, "Missing X-Request-ID header"

    # 2. Readiness Probe
    print_step("2. Checking Readiness Probe (/health/ready)")
    s, data, _ = http_request("GET", f"{API_URL}/health/ready")
    assert_status(s, 200, "Readiness Probe")

    # 3. User Registration
    print_step("3. Registering Test User")
    test_id = uuid.uuid4().hex[:8]
    email = f"smoke_test_{test_id}@example.com"
    password = f"P@ssw0rd_{test_id}!"
    s, data, _ = http_request(
        "POST",
        f"{API_URL}/auth/register",
        data={"email": email, "password": password, "name": f"Smoke Test {test_id}"},
    )
    assert_status(s, 201, "User Registration")


    # 4. User Login
    print_step("4. User Login & Token Retrieval")
    s, data, _ = http_request(
        "POST",
        f"{API_URL}/auth/login",
        data={"email": email, "password": password},
    )
    assert_status(s, 200, "User Login")
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    # 5. Token Refresh
    print_step("5. Token Refresh Rotation")
    s, data, _ = http_request(
        "POST",
        f"{API_URL}/auth/refresh",
        data={"refresh_token": refresh_token},
    )
    assert_status(s, 200, "Token Refresh")
    access_token = data["access_token"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    # 6. Current User Me
    print_step("6. Fetching Current User (/auth/me)")
    s, data, _ = http_request("GET", f"{API_URL}/auth/me", headers=auth_headers)
    assert_status(s, 200, "Get Current User")
    assert data["email"] == email

    # 7. Create Workspace
    print_step("7. Creating Multi-Tenant Workspace")
    s, data, _ = http_request(
        "POST",
        f"{API_URL}/workspaces",
        headers=auth_headers,
        data={"name": f"Smoke WS {test_id}", "description": "Smoke Testing Workspace"},
    )
    assert_status(s, 201, "Workspace Creation")
    workspace_id = data["id"]

    # 8. Create Environment
    print_step("8. Creating Environment in Workspace")
    s, data, _ = http_request(
        "POST",
        f"{API_URL}/workspaces/{workspace_id}/environments",
        headers=auth_headers,
        data={"name": "Development", "key": "dev", "description": "Development environment"},
    )
    assert_status(s, 201, "Create Environment")
    dev_env_id = data["id"]

    # 9. Create Server
    print_step("9. Creating Server in Workspace")
    s, data, _ = http_request(
        "POST",
        f"{API_URL}/workspaces/{workspace_id}/servers",
        headers=auth_headers,
        data={
            "name": f"Smoke Server {test_id}",
            "environment_id": dev_env_id,
            "ip_address": "127.0.0.1",
            "ssh_port": 22,
            "username": "smoke_user",
        },
    )
    assert_status(s, 201, "Server Creation")


    # 10. Audit Log Query
    print_step("10. Verifying Audit Log Records")
    s, data, _ = http_request("GET", f"{API_URL}/workspaces/{workspace_id}/audit-logs", headers=auth_headers)
    assert_status(s, 200, "Query Audit Logs")
    items = data.get("items", [])
    total = data.get("total", len(items))
    print(f" [INFO] Retrieved {len(items)} audit log items (total: {total})")

    print("\n==========================================================")
    print(" ALL PRODUCTION SMOKE TESTS COMPLETED SUCCESSFULLY! [OK]")
    print("==========================================================")



if __name__ == "__main__":
    main()
