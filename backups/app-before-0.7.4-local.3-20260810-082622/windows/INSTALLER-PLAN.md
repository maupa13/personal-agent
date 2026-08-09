# Windows Setup.exe contract

The future `RusPersonalAgent-Setup.exe` is a delivery shell over this exact Docker runtime, not a second product.

It must: detect/check Docker+WSL2, create `.env`, pull published images, `docker compose up -d`, wait for `/api/health`, create Start-menu/Desktop entries, configure optional startup, and open the browser. It must consume structured progress events and show technical status separately from optional personality/flavor messages in `INSTALLER-PERSONALITY.json`.

It must never expose raw model IDs to USER. Model selection remains in `/admin`.
