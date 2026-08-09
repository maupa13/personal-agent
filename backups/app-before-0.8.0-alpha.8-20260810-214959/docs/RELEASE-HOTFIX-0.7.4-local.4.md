# Personal Agent Rus 0.7.4-local.4 — Code sandbox execution permission hotfix

## Observed Windows failure

The real Windows reference run reached all of these milestones successfully:

- Ollama ready;
- SearXNG + Browser ready;
- Code Worker image built and socket health ready;
- Core image `0.7.4-local.3` built and ready;
- real inference PASS;
- Web capability/SSRF smoke PASS.

The launch then failed at the first real Code execution with `Real Code sandbox smoke failed.`

## Root cause

The Code worker deliberately drops all Linux capabilities and only adds back `CHOWN`, `SETUID`, `SETGID` and `KILL`. In particular it does **not** retain `CAP_DAC_OVERRIDE`.

The old job setup did this:

```text
mkdir job
chown job -> runner:runner
chmod job -> 0700
root supervisor writes main.py
```

A UID 0 process without `CAP_DAC_OVERRIDE` is still subject to normal directory access checks. After the directory became `0700` and runner-owned, the supervisor could no longer create the source file. The job therefore transitioned immediately to `FAILED`, while `/health` remained healthy because the socket and binaries existed.

The defect was reproduced outside Docker by dropping `CAP_DAC_OVERRIDE` from the supervisor and using a different runner UID/GID. The `0.7.4-local.3` worker failed with `PermissionError: [Errno 13] Permission denied: .../main.py`; the patched worker completed the same Python job and returned the expected stdout marker.

## Fix

Job directories now use:

```text
owner: root (supervisor)
group: runner
mode:  0770
```

This keeps the supervisor able to create and collect artifacts while the unprivileged runner receives only group access to its isolated job directory. `CAP_DAC_OVERRIDE` is **not** restored.

Additional hardening:

- normal `START`, `REPAIR` and baseline `VERIFY` degrade Code instead of aborting the whole local product when a real Code execution smoke fails;
- `CODE-ACCEPTANCE`, `FULL-ACCEPTANCE` and `RELEASE-ACCEPTANCE` remain fail-closed;
- Code smoke logs the returned job status/error/result when it fails;
- Code Worker logs startup state and non-sensitive job failure metadata.

## Upgrade behavior

Install/update preserves `.env`, Docker named volumes, workspace and artifacts. Existing local images are rebuilt/recreated under the `0.7.4-local.4` tags.
