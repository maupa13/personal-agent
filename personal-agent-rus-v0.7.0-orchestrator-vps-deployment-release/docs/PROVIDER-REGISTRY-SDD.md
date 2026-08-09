# Provider and Model Registry SDD

## Problem being fixed

The prototype Admin UI asks the administrator to type a raw model ID to add a model. That is not the intended product workflow.

On a machine that already has multiple models installed, Personal Agent must discover them automatically. External AI endpoints must be first-class provider connections.

## Architecture

```text
Provider Registry
  ├─ local-ollama (system-managed)
  ├─ external-ollama-* (optional)
  ├─ openai-compatible-*
  └─ future adapters
        ↓
Discovery adapters
        ↓
Unified Model Inventory
        ↓
Capability/Mode Router
```

## Provider entity

```text
id
name
type
base_url
enabled
managed_by (system|admin)
secret_ref
discovery_mode
health
last_discovered_at
created_at
updated_at
```

## Inventory entity

Inventory may be cached, but live discovery is authoritative for availability.

```text
provider_id
model_id
display_name
size
capabilities
available
source
metadata
last_seen_at
```

## Local Ollama discovery

Every Admin refresh calls `/api/tags` on configured Ollama provider. Existing Docker volume models automatically become available in inventory.

No extra registration step.

## External OpenAI-compatible discovery

Admin supplies connection metadata once. Test performs:

```text
GET /models
```

Successful models are merged into unified inventory.

## Managed downloads

Only providers that expose a managed pull API show a `Download model` action.

For Ollama:

```text
POST /api/pull
```

After pull completes, re-run discovery and use the discovered result.

## Routing

Routing is stored as:

```text
mode -> provider_id + model_id
```

Later capability routing becomes:

```text
capability + effort/profile -> route policy
```

## USER boundary

The following must never appear in USER endpoints or normal shell:

```text
provider_id
base_url
model_id
API key/secret ref
Docker/Ollama implementation details
```

## Acceptance IDs

```text
PRV-001 local Ollama auto-discovery
PRV-002 multiple installed local models shown
PRV-003 managed pull refreshes inventory
PRV-004 OpenAI-compatible connection test
PRV-005 OpenAI-compatible model discovery
PRV-006 provider/model route persistence
PRV-007 unavailable route failure/fallback
PRV-008 USER provider/model leakage blocked
PRV-009 secret redaction
PRV-010 provider removal safety
```
