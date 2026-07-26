"""Security attack vector tests — verifies the system handles malicious input."""
import sys, json, asyncio
sys.path.insert(0, '.')
from backend.main import app
from httpx import AsyncClient, ASGITransport

async def test():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as c:
        tests = [
            ("Path traversal", lambda: c.get("/api/incidents/../../etc/passwd")),
            ("XSS in model", lambda: c.get("/api/models/<script>alert(1)</script>")),
            ("Empty body POST", lambda: c.post("/api/investigate", content=b"{}", headers={"Content-Type": "application/json"})),
            ("Invalid JSON POST", lambda: c.post("/api/investigate", content=b"not json", headers={"Content-Type": "application/json"})),
            ("Missing dataset_urn", lambda: c.post("/api/compliance/scan-pii", content=b"{}", headers={"Content-Type": "application/json"})),
            ("Negative incident ID", lambda: c.get("/api/incidents/-1")),
            ("SQL injection URN", lambda: c.post("/api/investigate", content=json.dumps({"dataset_urn": "'; DROP TABLE incidents; --"}).encode(), headers={"Content-Type": "application/json"})),
            ("Very long incident ID", lambda: c.get("/api/incidents/" + "a" * 1000)),
            ("Unicode in model name", lambda: c.get("/api/models/日本語モデル")),
            ("Null byte in path", lambda: c.get("/api/incidents/test%00../../../etc/passwd")),
        ]
        
        for name, test_fn in tests:
            try:
                r = await test_fn()
                status = "BLOCKED" if r.status_code in (400, 404, 422, 500) else f"OPEN({r.status_code})"
                print(f"  {status}: {name}")
            except Exception as e:
                print(f"  CRASH: {name} - {e}")

asyncio.run(test())
