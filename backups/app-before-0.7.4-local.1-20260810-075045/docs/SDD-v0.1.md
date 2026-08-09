# Personal Agent Rus v0.1 — Docker Product Foundation

## Product invariant
Personal Agent Rus is the product. Docker, Ollama, model IDs, containers and provider details are implementation/admin concerns and must not appear in the ordinary USER surface.

## Scope
This milestone proves one complete vertical slice:

USER browser -> Personal Agent Core -> internal routing -> local inference -> answer.

ADMIN browser -> authenticated admin API -> installed-model inventory / model pull / mode routing.

Persistent Docker volumes retain model data and Personal Agent configuration across container restart/recreate.

## User contract
- Entry point: `http://127.0.0.1:3100/` by default.
- USER sees `Авто`, `Быстро`, `Умно`, not model identifiers.
- USER can chat immediately after bootstrap completes.
- USER-facing API responses must not contain internal model IDs.

## Admin contract
- Entry point: `/admin`.
- Requires local admin token generated into `.env`.
- ADMIN can inspect installed models, pull a model, and map USER modes to models.
- Raw model identifiers are allowed only here.

## Bootstrap model contract
`qwen3:0.6b` is a smoke/bootstrap dependency only. It exists to prove the inference path and provide a working fallback. It is not the product's mandatory quality model. Production-quality model assignments are ADMIN configuration.

## Persistence
Named volumes:
- `par-rus-data`: SQLite configuration/state.
- `par-rus-models`: local model store.

No normal start/stop/update command may use `down -v`, `volume prune`, or `system prune`.

## Release gate
v0.1 is accepted only when static checks, HTTP integration acceptance, Docker Compose validation, Core image build, real Docker health, real inference smoke, restart persistence, USER leakage checks, and ADMIN routing checks pass on the reference Windows machine.
