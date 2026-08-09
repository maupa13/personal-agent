"""Auth package boundary for authentication and authorization helpers."""

from __future__ import annotations

from typing import Any


class EntitlementError(Exception):
    """Raised when access to an entitlement is denied."""


def effective_entitlements(db_path: str, *, plan_id: str) -> dict[str, Any]:
    """Compatibility stub for older imports.

    The active entitlement implementation lives in
    `app.services.core.app.entitlement_service`.
    """

    raise NotImplementedError(
        "Use app.services.core.app.entitlement_service.EntitlementService instead."
    )


__all__ = ["EntitlementError", "effective_entitlements"]
