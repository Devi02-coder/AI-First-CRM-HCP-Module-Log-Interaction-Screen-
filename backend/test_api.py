"""
Quick end-to-end API test to verify the backend is working.
"""
import urllib.request
import urllib.error
import json

BASE = "http://localhost:8000"

def test_endpoint(method, path, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            print(f"  [OK] {method} {path} -> {resp.status}")
            return result
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        print(f"  [HTTP {e.code}] {method} {path} -> {body_text[:200]}")
    except Exception as e:
        print(f"  [FAIL] {method} {path} -> {e}")

print("=" * 60)
print("  HCP CRM Backend API Integration Test")
print("=" * 60)

print("\n-- GET /api/interactions --")
interactions = test_endpoint("GET", "/api/interactions")
if interactions is not None:
    print(f"     Found {len(interactions)} interactions in database.")

print("\n-- GET /api/chat/history --")
history = test_endpoint("GET", "/api/chat/history")
if history is not None:
    print(f"     Found {len(history)} chat messages.")

print("\n-- GET /api/audit-logs --")
audit = test_endpoint("GET", "/api/audit-logs")
if audit is not None:
    print(f"     Found {len(audit)} audit log entries.")

print("\n-- GET /api/tool-logs --")
tools = test_endpoint("GET", "/api/tool-logs")
if tools is not None:
    print(f"     Found {len(tools)} tool execution logs.")

print("\n-- POST /api/chat (AI Agent Test) --")
chat_resp = test_endpoint("POST", "/api/chat", {
    "message": "Met Dr. Sarah Johnson today at Apollo Hospital. Discussed CardioMax and HeartPlus. She was very positive and interested in clinical trials. Shared efficacy brochure. Follow up next Tuesday."
})
if chat_resp:
    print(f"     Agent Response: {chat_resp.get('response', '')[:120]}...")
    print(f"     Tool Used: {chat_resp.get('current_tool')}")
    print(f"     Validation: {chat_resp.get('validation_status')}")
    logs = chat_resp.get('tool_execution_logs', [])
    print(f"     Tool Steps Executed: {len(logs)}")
    for log in logs:
        print(f"       ✓ {log.get('step', '')} — {log.get('status', '')[:60]}")

print("\n-- GET /api/interactions (After Logging) --")
interactions2 = test_endpoint("GET", "/api/interactions")
if interactions2 is not None:
    print(f"     Now found {len(interactions2)} interactions.")
    if interactions2:
        intr = interactions2[0]
        print(f"     Latest: {intr.get('hcp_name')} @ {intr.get('hospital_clinic')} | Sentiment: {intr.get('sentiment')}")

print("\n-- POST /api/chat (Edit Test) --")
edit_resp = test_endpoint("POST", "/api/chat", {
    "message": "Change sentiment to Neutral"
})
if edit_resp:
    print(f"     Edit Response: {edit_resp.get('response', '')[:120]}...")

print("\n" + "=" * 60)
print("  API Integration Test Complete!")
print("=" * 60)
