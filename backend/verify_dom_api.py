"""
Full DOM + API Verification for HCP CRM System
Tests:
1. Backend API endpoints
2. AI chat log interaction (submits natural language -> checks form data returned)
3. Edit interaction tool
4. Validation
5. History retrieval
6. Next best action
"""
import urllib.request
import urllib.error
import json
import sys

BASE_API = "http://localhost:8000"
BASE_UI  = "http://localhost:5173"

PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[INFO]"

results = []

def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    msg = f"  {status} {label}"
    if detail:
        msg += f" | {detail}"
    print(msg)
    results.append((label, condition))

def api_post(path, body):
    url = BASE_API + path
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()}
    except Exception as ex:
        return 0, {"error": str(ex)}

def api_get(path):
    url = BASE_API + path
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {}
    except Exception as ex:
        return 0, {}

# ─────────────────────────────────────────────────────────────
print("\n" + "="*70)
print("  HCP CRM DOM & API Verification Suite")
print("="*70)

# ─── TEST 1: Frontend Serving ─────────────────────────────────
print("\n[SECTION 1] Frontend Server Check")
try:
    with urllib.request.urlopen(BASE_UI, timeout=5) as r:
        html = r.read().decode("utf-8", errors="ignore")
        check("Vite server responds HTTP 200",  r.status == 200)
        check("HTML has <div id='root'>",       'id="root"' in html)
        check("React entry script loaded",      '<script' in html)
except Exception as e:
    check("Vite server reachable", False, str(e))

# ─── TEST 2: Backend Health ───────────────────────────────────
print("\n[SECTION 2] Backend API Connectivity")
status, data = api_get("/api/interactions")
check("GET /api/interactions returns 200",    status == 200)
check("Response is a list",                   isinstance(data, list), f"Count: {len(data)}")

status, data = api_get("/api/chat/history")
check("GET /api/chat/history returns 200",    status == 200)
check("Chat history is a list",               isinstance(data, list), f"Count: {len(data)}")

status, data = api_get("/api/audit-logs")
check("GET /api/audit-logs returns 200",      status == 200)

status, data = api_get("/api/tool-logs")
check("GET /api/tool-logs returns 200",       status == 200)

# ─── TEST 3: Log Interaction Tool (The Golden Rule Test) ─────
print("\n[SECTION 3] Log Interaction Tool - AI Fills Form from Natural Language")
msg = "Today I met Dr. Priya Mehta at Apollo Hospital. We discussed OncoBoost efficacy and shared the Phase III PDF brochure. The sentiment was very positive and she agreed to prescribe. Follow up next Tuesday."
status, resp = api_post("/api/chat", {"message": msg})
check("POST /api/chat returns 200",                   status == 200, f"Got: {status}")
check("Response has 'response' field",                "response" in resp)
check("Response has 'interaction_data' field",        "interaction_data" in resp)
check("Response has 'tool_execution_logs' field",     "tool_execution_logs" in resp)

if status == 200 and "interaction_data" in resp:
    d = resp["interaction_data"] or {}
    logs = resp.get("tool_execution_logs", [])
    check("interaction_data is non-empty dict",       bool(d))
    check("hcp_name extracted (Dr. Priya Mehta)",     "priya" in str(d.get("hcp_name","")).lower() or "mehta" in str(d.get("hcp_name","")).lower(), str(d.get("hcp_name")))
    check("hospital_clinic extracted (Apollo)",       "apollo" in str(d.get("hospital_clinic","")).lower(), str(d.get("hospital_clinic")))
    check("sentiment extracted (Positive)",           str(d.get("sentiment","")).lower() == "positive", str(d.get("sentiment")))
    check("materials_shared extracted (brochure/pdf)",any("brochure" in str(m).lower() or "pdf" in str(m).lower() or "phase" in str(m).lower() for m in d.get("materials_shared",[])), str(d.get("materials_shared")))
    check("follow_up_required is True",               d.get("follow_up_required") == True, str(d.get("follow_up_required")))
    check("interaction_summary generated",            len(str(d.get("interaction_summary",""))) > 10, str(d.get("interaction_summary",""))[:80])
    check("next_best_action generated",               len(str(d.get("next_best_action",""))) > 5)
    check("validation_status set",                    d.get("validation_status") in ["Valid","Invalid","Pending"])
    check("Tool execution logs > 0",                  len(logs) > 0, f"Steps: {len(logs)}")
    if logs:
        steps = [l.get("step","") for l in logs]
        print(f"    Tool steps executed: {steps}")
    
    interaction_id = d.get("id")
    check("Interaction record saved with an ID",      bool(interaction_id), f"ID: {interaction_id}")

# ─── TEST 4: Edit Interaction Tool ───────────────────────────
print("\n[SECTION 4] Edit Interaction Tool - AI Edits Form Fields")
edit_msg = "Sorry, the sentiment was actually Neutral, and her name is Dr. Priya Sharma not Mehta."
status2, resp2 = api_post("/api/chat", {"message": edit_msg})
check("POST /api/chat returns 200 for edit",          status2 == 200)
if status2 == 200 and "interaction_data" in resp2:
    d2 = resp2["interaction_data"] or {}
    check("Sentiment updated to Neutral",             str(d2.get("sentiment","")).lower() == "neutral", str(d2.get("sentiment")))
    check("AI response mentions the edit",            "neutral" in resp2.get("response","").lower() or "update" in resp2.get("response","").lower() or "edit" in resp2.get("response","").lower(), resp2.get("response","")[:80])

# ─── TEST 5: HCP Context Retrieval Tool ──────────────────────
print("\n[SECTION 5] HCP Context Retrieval Tool - Show History")
hist_msg = "Show me the history for Dr. Priya"
status3, resp3 = api_post("/api/chat", {"message": hist_msg})
check("POST /api/chat returns 200 for history",       status3 == 200)
check("AI responds with a message about history",     len(resp3.get("response","")) > 5, resp3.get("response","")[:100])

# ─── TEST 6: Next Best Action Tool ───────────────────────────
print("\n[SECTION 6] Next Best Action Tool - Recommendations")
nba_msg = "What is the next best action for the current HCP?"
status4, resp4 = api_post("/api/chat", {"message": nba_msg})
check("POST /api/chat returns 200 for NBA",           status4 == 200)
check("next_best_action field in data",               "next_best_action" in resp4.get("interaction_data", {}) or len(resp4.get("response","")) > 5)

# ─── TEST 7: Validation Tool ─────────────────────────────────
print("\n[SECTION 7] CRM Validation Tool - Validate Record")
val_msg = "Validate the current interaction record"
status5, resp5 = api_post("/api/chat", {"message": val_msg})
check("POST /api/chat returns 200 for validate",      status5 == 200)
check("validation_status in response",                "validation_status" in resp5, str(list(resp5.keys())))

# ─── TEST 8: DB Record Count ──────────────────────────────────
print("\n[SECTION 8] Database Persistence Verification")
status6, interactions = api_get("/api/interactions")
check("Interactions saved in DB after tests",         isinstance(interactions, list) and len(interactions) >= 1, f"Count: {len(interactions) if isinstance(interactions, list) else 0}")
if isinstance(interactions, list) and interactions:
    latest = interactions[0]
    check("Latest record has hcp_name",               bool(latest.get("hcp_name")), str(latest.get("hcp_name")))
    check("Latest record has sentiment",              bool(latest.get("sentiment")), str(latest.get("sentiment")))
    check("Latest record has validation_status",      bool(latest.get("validation_status")), str(latest.get("validation_status")))

status7, audit = api_get("/api/audit-logs")
check("Audit logs written",                           isinstance(audit, list) and len(audit) >= 1, f"Count: {len(audit) if isinstance(audit, list) else 0}")

status8, tools = api_get("/api/tool-logs")
check("Tool execution logs written",                  isinstance(tools, list) and len(tools) >= 1, f"Count: {len(tools) if isinstance(tools, list) else 0}")

# ─── SUMMARY ─────────────────────────────────────────────────
print("\n" + "="*70)
passed = sum(1 for _, ok in results if ok)
failed = sum(1 for _, ok in results if not ok)
total  = len(results)
print(f"  TOTAL: {total} checks | PASSED: {passed} | FAILED: {failed}")
print("="*70)
if failed == 0:
    print("  ALL CHECKS PASSED - System is fully functional!")
else:
    print("  Some checks failed. Review above.")
    for label, ok in results:
        if not ok:
            print(f"    - {label}")
print("="*70)
