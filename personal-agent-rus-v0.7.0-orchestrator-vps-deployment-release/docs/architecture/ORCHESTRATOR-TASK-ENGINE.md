# Orchestrator / Task Engine — v0.7.0

## Purpose

Personal Agent Rus must execute long/multi-capability requests as durable tasks rather than one HTTP request.

Current vertical slice implements `research_report`:

```text
QUESTION
→ WEB RESEARCH
→ VERIFIED SOURCES
→ MODEL ANALYSIS
→ MD
→ XLSX
→ PDF
→ REOPEN / SHA256 VERIFICATION
→ COMPLETED
```

## Durable model

SQLite tables:

- `tasks`
- `task_steps`
- `task_events`

Task states currently executable:

`CREATED → PLANNING → RUNNING → VERIFYING → COMPLETED`

Terminal error states: `FAILED`, `CANCELLED`.

The schema remains compatible with future `QUEUED`, `RETRYING`, `WAITING_PERMISSION`, `WAITING_USER`, `PARTIAL`, `BLOCKED` states from MASTER-SPEC.

Each step records input/output/status and completed steps are skipped on restart. Generated artifacts are referenced by immutable artifact ID + SHA256, which prevents a recovered task from silently duplicating a verified step.

## API

- `POST /api/tasks`
- `GET /api/tasks`
- `GET /api/tasks/{id}`
- `GET /api/tasks/{id}/events` (SSE one-shot/reconnect transport)
- `GET /api/tasks/{id}/events?format=json&after=<eventId>`
- `POST /api/tasks/{id}/cancel`

Task truth is server-side. Browser state is only a view.

## User progress

User-visible phases do not expose chain-of-thought:

- Планирую
- Ищу источники
- Анализирую
- Создаю файлы
- Проверяю результат
- Готово

## Known scope boundary

v0.7.0 proves the durable task foundation with one real multi-capability workflow. It does **not** claim the whole future planner/tool DAG is complete. Future task types must use the same persisted step/event/verification contract and add mandatory USER E2E before becoming `ready`.
