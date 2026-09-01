from __future__ import annotations

from services.core.app.observability_service import StructuredLogger


def test_structured_logger_writes_and_queries(tmp_path):
    logger = StructuredLogger(tmp_path, service="core", version="1.0.1")

    logger.event("chat.completed", request_id="req-1", correlation_id="corr-1", token="secret")
    logger.event("chat.failed", level="error", request_id="req-2", correlation_id="corr-2", payload={"message": "ok"})

    all_events = logger.tail()
    assert len(all_events) == 2
    assert all_events[0]["service"] == "core"
    assert all_events[0]["version"] == "1.0.1"
    assert all_events[0]["token"] == "[REDACTED]"

    matched = logger.query(level="error", request_id="req-2")
    assert len(matched) == 1
    assert matched[0]["event"] == "chat.failed"

