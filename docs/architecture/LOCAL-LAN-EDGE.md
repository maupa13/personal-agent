# Local / LAN / Edge contract

## Local default

`PA_BIND_IP=127.0.0.1` keeps Personal Agent private to the workstation.

## Windows LAN mode

The existing local Docker product remains supported.

Commands:

- `LAN-ENABLE.cmd`
- `LAN-STATUS.cmd`
- `LAN-DISABLE.cmd`

Enable performs:

1. changes only `PA_BIND_IP` to `0.0.0.0`;
2. creates a Windows Firewall inbound rule only for the configured UI TCP port and **Private** network profile;
3. recreates Core without deleting volumes;
4. prints detected LAN URLs.

Disable restores localhost binding and removes the dedicated firewall rule.

LAN HTTP is sufficient for chat/file flows. Browser microphone/camera APIs may require a Secure Context; future mobile/audio release must provide LAN HTTPS/pairing rather than pretending insecure HTTP grants all permissions.

## Personal Agent Edge (next slice)

Goal: make the local GPU/files extension installable instead of requiring users to manually assemble Docker services.

Planned UX:

```text
Install Personal Agent Edge
→ sign in / enter pairing code
→ outbound encrypted connection to user's VPS/cloud account
→ detect local GPU/models/workspaces
→ admin grants capabilities
→ router can use local worker according to privacy policy
```

The Edge service must initiate outbound connectivity. A home router port-forward is not an acceptable default setup.
