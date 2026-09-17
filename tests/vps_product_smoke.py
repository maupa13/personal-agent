"""Run inside Core after deploy. Real AI calls; cleans its files and temporary session.

docker compose ... exec -T core python /tmp/vps_product_smoke.py
Requires administrator shell access; never prints a credential or user content.
"""
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, "/app")
import main as app

BASE = "http://127.0.0.1:8080"
with app.db() as conn:
    owner = conn.execute("SELECT id FROM users WHERE role='OWNER' AND status='active' ORDER BY created_at LIMIT 1").fetchone()
assert owner, "active owner required"
token, _ = app.create_session(owner["id"], ip="127.0.0.1", user_agent="Product repair acceptance")
headers = {"Cookie": "pa_session=" + token, "X-CSRF-Token": app.csrf_token_for_session(token), "Content-Type": "application/json"}
artifacts, jobs, tasks, results = [], [], [], []


def call(path, body=None, method=None):
    request = urllib.request.Request(BASE + path, data=json.dumps(body).encode() if body is not None else None,
                                     headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)


def check(name, fn):
    if len(sys.argv) > 1 and name not in sys.argv[1:]:
        return
    started = time.monotonic()
    try:
        detail = fn()
        result = {"test": name, "status": "PASS", "detail": detail}
    except Exception as exc:
        result = {"test": name, "status": "FAIL", "error_type": type(exc).__name__}
        if isinstance(exc, AssertionError):
            result["reason"] = str(exc)[:250]
        if isinstance(exc, urllib.error.HTTPError):
            result["http_status"] = exc.code
            try:
                result["error"] = json.load(exc).get("error", "")[:250]
            except Exception:
                pass
    result["seconds"] = round(time.monotonic() - started, 2)
    results.append(result)
    print(json.dumps(result, ensure_ascii=False), flush=True)


def chat(mode):
    value = call("/api/chat", {"mode": mode, "messages": [{"role": "user", "content": "Ответь кратко: сколько будет два плюс два?"}]})
    assert value["message"]["content"].strip()
    return {"mode": mode, "nonempty": True}


def files():
    payloads = {"txt": "Smoke marker 4815", "md": "# Smoke marker 4815", "json": {"smoke": 4815},
                "csv": {"headers": ["value"], "rows": [[4815]]}, "pdf": "Smoke marker 4815",
                "docx": {"title": "Smoke", "paragraphs": ["Marker 4815"]},
                "xlsx": {"headers": ["value"], "rows": [[4815]]}, "pptx": {"title": "Smoke", "paragraphs": ["Marker 4815"]}}
    for fmt, content in payloads.items():
        value = call("/api/files/create", {"format": fmt, "name": f"repair-smoke.{fmt}", "content": content})["artifact"]
        artifacts.append(value["artifact_id"])
        assert value["validation_status"] == "verified" and value["size"] > 0
        detail = call("/api/files/" + value["artifact_id"])
        assert detail["artifact"]["text"] is not None
        time.sleep(1.1)  # production upload/create throttle
    answer = call("/api/files/" + artifacts[0] + "/analyze", {"question": "Назови номер маркера из файла. Ответь только числом."})
    assert "4815" in answer["answer"]
    return {"verified_formats": list(payloads), "openai_file_analysis": True}


def code(language, source):
    value = call("/api/code/jobs", {"language": language, "code": source, "timeout_seconds": 10})["job"]
    jobs.append(value["id"])
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        value = call("/api/code/jobs/" + value["id"])["job"]
        if value["status"] in {"COMPLETED", "FAILED", "CANCELLED"}:
            break
        time.sleep(.3)
    assert value["status"] == "COMPLETED", value.get("error")
    assert "42" in json.dumps(value)
    return {"language": language, "completed": True}


def search():
    value = call("/api/web/search", {"query": "Python programming official documentation", "limit": 3})
    assert value["results"]
    return {"sources": len(value["results"])}


def read():
    value = call("/api/web/read", {"url": "https://www.python.org/about/"})
    assert len(value["page"]["text"]) > 500
    assert "Python" in value["page"]["text"]
    assert value["page"]["text"].count("\ufffd") < len(value["page"]["text"]) // 100
    return {"strategy": value["page"]["strategy"], "characters": len(value["page"]["text"])}


def research():
    value = call("/api/research", {"question": "Какие основные возможности Python описаны на официальном сайте python.org?", "max_sources": 3, "mode": "smart"})
    assert value["answer"].strip() and value["sources"]
    return {"sources": len(value["sources"]), "nonempty": True}


def report_task():
    task = call("/api/tasks", {"type": "research_report", "question": "Краткий отчёт о возможностях Python по https://www.python.org/about/ и https://docs.python.org/3/tutorial/", "formats": ["md", "xlsx", "pdf"]})["task"]
    tasks.append(task["id"])
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        task = call("/api/tasks/" + task["id"])["task"]
        if task["status"] in {"COMPLETED", "FAILED", "CANCELLED"}:
            break
        time.sleep(1)
    assert task["status"] == "COMPLETED", task.get("error")
    files = task["result"]["artifacts"]
    assert {item["name"].rsplit(".", 1)[-1] for item in files} == {"md", "xlsx", "pdf"}
    assert all(item["validation_status"] == "verified" for item in files)
    return {"completed": True, "verified_exports": ["md", "xlsx", "pdf"], "sources": len(task["result"]["sources"])}


try:
    before = call("/api/billing/me")
    assert before["subscription"]["billing_exempt"]
    check("health", lambda: call("/api/health"))
    for mode in ["auto", "fast", "smart", "auto"]:
        check("chat_" + mode, lambda mode=mode: chat(mode))
    check("files_eight_formats_and_analysis", files)
    check("code_python", lambda: code("python", "print(6 * 7)"))
    check("code_java", lambda: code("java", 'public class Main { public static void main(String[] a) { System.out.println(42); } }'))
    check("code_powershell", lambda: code("powershell", "Write-Output (6 * 7)"))
    check("web_search", search)
    check("web_read", read)
    check("research_with_sources", research)
    check("research_report_task", report_task)
    assert call("/api/billing/me")["balance"] == before["balance"], "smoke must not alter the wallet"
finally:
    for task_id in tasks:
        task = call("/api/tasks/" + task_id)["task"]
        if task["status"] not in {"COMPLETED", "FAILED", "CANCELLED"}:
            call("/api/tasks/" + task_id + "/cancel", {})
            print(json.dumps({"cleanup": "task cancellation requested", "status": "PARTIAL"}), flush=True)
            continue
        for step in task.get("steps", []):
            artifact_id = (step.get("output") or {}).get("artifact_id")
            if artifact_id and artifact_id not in artifacts:
                artifacts.append(artifact_id)
        with app.db() as conn:
            conn.execute("DELETE FROM task_events WHERE task_id=?", (task_id,))
            conn.execute("DELETE FROM task_steps WHERE task_id=?", (task_id,))
            conn.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (task_id, owner["id"]))
            conn.commit()
    for artifact in artifacts:
        try:
            call("/api/files/" + artifact, method="DELETE")
        except Exception:
            print(json.dumps({"cleanup": "artifact", "status": "FAIL"}), flush=True)
    with app.db() as conn:
        conn.execute("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),))
        for job in jobs:
            conn.execute("DELETE FROM code_jobs WHERE id=? AND user_id=?", (job, owner["id"]))
        conn.commit()
sys.exit(1 if any(x["status"] == "FAIL" for x in results) else 0)
