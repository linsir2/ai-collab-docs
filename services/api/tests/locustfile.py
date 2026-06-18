"""Locust performance test for the ai-collab-docs backend.

User classes:
  A. OwnerUser    (weight 2)  - owner@demo.com  / demo123
  B. EditorUser   (weight 3)  - editor@demo.com / demo123
  C. ReaderUser   (weight 5)  - reader@demo.com / demo123
  D. AnonymousUser(weight 1)  - brute-force login simulation + health check

Run headless:
  uv run locust -f tests/locustfile.py --headless -u 50 -r 5 -t 30s \
      --host http://127.0.0.1:8000
"""

import json
import random
import string

from locust import HttpUser, between, task


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

DEMO_DOC_ID = "doc_demo_001"


def _login(client, email: str, password: str) -> str | None:
    """Authenticate against /api/auth/login and return the access token."""
    with client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
        name="POST /api/auth/login",
        catch_response=True,
    ) as resp:
        if resp.status_code == 200:
            try:
                return resp.json().get("access_token")
            except (json.JSONDecodeError, KeyError):
                return None
        # Non-200 (e.g. 401 / 429) is expected for some users - mark as success
        # so it does not skew the failure stats for the login call itself.
        resp.success()
        return None


def _auth_headers(token: str | None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


# ---------------------------------------------------------------------------
# A. OwnerUser
# ---------------------------------------------------------------------------

class OwnerUser(HttpUser):
    weight = 2
    wait_time = between(1, 3)

    def on_start(self):
        self.token = _login(self.client, "owner@demo.com", "demo123")

    @task(3)
    def list_documents(self):
        self.client.get("/api/documents", name="GET /api/documents", headers=_auth_headers(self.token))

    @task(2)
    def get_document(self):
        self.client.get(
            f"/api/documents/{DEMO_DOC_ID}",
            name="GET /api/documents/doc_demo_001",
            headers=_auth_headers(self.token),
        )

    @task(1)
    def list_forge_proposals(self):
        self.client.get(
            "/api/forge/proposals",
            name="GET /api/forge/proposals?doc_id=doc_demo_001",
            params={"doc_id": DEMO_DOC_ID},
            headers=_auth_headers(self.token),
        )

    @task(1)
    def list_audit_logs(self):
        self.client.get("/api/audit/logs", name="GET /api/audit/logs", headers=_auth_headers(self.token))


# ---------------------------------------------------------------------------
# B. EditorUser
# ---------------------------------------------------------------------------

class EditorUser(HttpUser):
    weight = 3
    wait_time = between(1, 3)

    def on_start(self):
        self.token = _login(self.client, "editor@demo.com", "demo123")

    @task(3)
    def list_documents(self):
        self.client.get("/api/documents", name="GET /api/documents", headers=_auth_headers(self.token))

    @task(1)
    def forge_refine(self):
        block_suffix = "".join(random.choices(string.ascii_lowercase, k=6))
        self.client.post(
            "/api/forge/refine",
            name="POST /api/forge/refine",
            json={
                "doc_id": DEMO_DOC_ID,
                "block_id": f"blk_{block_suffix}",
                "instruction": "润色这一段，使其更简洁",
                "ai_source": "mock-llm",
            },
            headers=_auth_headers(self.token),
        )

    @task(2)
    def get_document(self):
        self.client.get(
            f"/api/documents/{DEMO_DOC_ID}",
            name="GET /api/documents/doc_demo_001",
            headers=_auth_headers(self.token),
        )


# ---------------------------------------------------------------------------
# C. ReaderUser
# ---------------------------------------------------------------------------

class ReaderUser(HttpUser):
    weight = 5
    wait_time = between(1, 3)

    def on_start(self):
        self.token = _login(self.client, "reader@demo.com", "demo123")

    @task(2)
    def list_documents(self):
        self.client.get("/api/documents", name="GET /api/documents", headers=_auth_headers(self.token))

    @task(3)
    def get_document(self):
        self.client.get(
            f"/api/documents/{DEMO_DOC_ID}",
            name="GET /api/documents/doc_demo_001",
            headers=_auth_headers(self.token),
        )


# ---------------------------------------------------------------------------
# D. AnonymousUser - brute-force login simulation + health check
# ---------------------------------------------------------------------------

class AnonymousUser(HttpUser):
    weight = 1
    wait_time = between(1, 3)

    # No on_start login - this user stays anonymous.

    @task(3)
    def brute_force_login(self):
        # Rotate through a small set of bogus credentials to simulate a
        # brute-force attack against the login endpoint.
        bogus_emails = [
            "attacker@evil.com",
            "admin@admin.com",
            "root@root.com",
            "test@test.com",
            "hacker@dark.net",
        ]
        bogus_passwords = ["password", "123456", "admin", "letmein", "qwerty"]
        self.client.post(
            "/api/auth/login",
            name="POST /api/auth/login (brute-force)",
            json={
                "email": random.choice(bogus_emails),
                "password": random.choice(bogus_passwords),
            },
        )

    @task(1)
    def health_check(self):
        self.client.get("/health", name="GET /health")
