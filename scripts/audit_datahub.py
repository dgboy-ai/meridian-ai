"""Audit DataHub integration status."""
import os

print("=== DATAHUB INTEGRATION AUDIT ===")

# 1. Check MCP Server
with open("backend/mcp_server.py") as f:
    c = f.read()
    print(f"MCP Server: {'MeridianMCPServer' in c}")
    print(f"MCP Protocol: {'jsonrpc' in c}")
    print(f"MCP Tools: {'meridian_investigate' in c}")

# 2. Check DataHub client
with open("backend/clients/datahub_client.py") as f:
    c = f.read()
    print(f"DataHub GMS URL: {'gms_url' in c}")
    print(f"Mock mode: {'mock' in c.lower()}")
    print(f"Real HTTP calls: {'httpx' in c}")
    print(f"Async client: {'AsyncClient' in c}")

# 3. Check what DataHub tools we use
tools_used = []
content = open("backend/clients/datahub_client.py").read()
for tool in ["search", "get_lineage", "list_schema_fields", "save_document",
             "add_structured_properties", "raise_incident", "batch_add_tags",
             "get_entities", "search_documents"]:
    if tool in content:
        tools_used.append(tool)
print(f"DataHub tools used: {tools_used}")

# 4. Check Actions Framework
with open("backend/actions/listener.py") as f:
    c = f.read()
    print(f"Actions Framework: {'ActionsListener' in c}")

# 5. Check YAML config
yaml_path = "config/actions/meridian_auto_trigger.yaml"
print(f"Actions YAML exists: {os.path.exists(yaml_path)}")

# 6. Check what writes to DataHub
print("\n=== DATAHUB WRITE OPERATIONS ===")
for root, dirs, files in os.walk("backend/workers"):
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            with open(path) as fh:
                content = fh.read()
                writes = []
                if "save_document" in content:
                    writes.append("save_document")
                if "add_structured_properties" in content:
                    writes.append("add_structured_properties")
                if "raise_incident" in content:
                    writes.append("raise_incident")
                if "batch_add_tags" in content:
                    writes.append("batch_add_tags")
                if writes:
                    print(f"  {f}: {writes}")

# 7. Check mock vs real
print("\n=== MOCK vs REAL ===")
with open("backend/clients/datahub_client.py") as f:
    c = f.read()
    if "_connected = True" in c:
        print("Real mode: Can connect to DataHub GMS")
    if "MOCK_ENTITIES" in c:
        print("Mock mode: Fallback entities available")
    if "_probe_gms" in c:
        print("Auto-detection: Probes GMS on startup")
