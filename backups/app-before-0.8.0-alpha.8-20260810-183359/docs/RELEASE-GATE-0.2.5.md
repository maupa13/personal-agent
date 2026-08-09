# Release Gate — Personal Agent Rus 0.2.5

Scope: structured presets + provider/model discovery + external provider connections + registration/session foundation.

## New product behavior

### Starter presets

`Объяснить / Написать / Проанализировать` are structured presets sent to Core as `preset=explain|write|analyze`. They are independent from `Авто/Быстро/Умно`.

### Model/provider UX

The previous manual-model-ID-first Admin workflow is removed as the primary path.

Admin workflow:

```text
Провайдеры
→ автоматическое обнаружение моделей
→ Модели
→ Маршрутизация
```

`local-ollama` is system managed and automatically discovers every model already installed in the Ollama Docker volume.

OpenAI-compatible endpoints (including LM Studio when its OpenAI-compatible server is enabled) can be added once. `/models` discovery populates unified inventory automatically.

Routing now persists `(provider_id, model_id)`.

### Registration

Browser pages now exist:

```text
/register
/login
/account
```

Default local profile remains `PA_AUTH_MODE=personal`, where USER registration is not required.

For multi-user/server testing:

```text
PA_AUTH_MODE=accounts
PA_REGISTRATION_POLICY=open
```

then registration/login/session becomes mandatory for USER chat.

## Local automated evidence

Required local release gate includes:

- static/hygiene;
- Windows command contract static verification;
- public boundary;
- structured presets;
- local Ollama multi-model auto-discovery;
- OpenAI-compatible provider creation/test/discovery;
- provider secret redaction;
- provider+model routing;
- managed Ollama pull and inventory refresh;
- route/provider persistence after Core restart;
- accounts-mode registration/login/logout/session;
- personal-mode anonymous local profile;
- concurrency;
- capability honesty;
- Chromium USER shell;
- Chromium Admin Providers/Models/Routing/Users;
- backend-controlled model-name XSS resistance.

Reference-Windows real runtime/lifecycle remains a separate authoritative gate after package installation.
