"""
MockModuleClient — test/development adapter.

Used when USE_MOCK_ADAPTERS=true (CI, offline dev, standalone demo).
Always reports the service as UNAVAILABLE with is_mock=True.
Does NOT pretend the service is HEALTHY.
"""
from __future__ import annotations

from typing import Any

from backend.app.integrations.module_client import (
    HealthStatus,
    ModuleClient,
    ServiceHealthResult,
)


class MockModuleClient(ModuleClient):
    """Mock adapter — clearly marks itself as a mock. Used in test/CI only."""

    def __init__(self, service_name: str) -> None:
        self._service_name = service_name

    @property
    def service_name(self) -> str:
        return self._service_name

    @property
    def base_url(self) -> str | None:
        return None

    async def get_health(self) -> ServiceHealthResult:
        return ServiceHealthResult(
            service=self._service_name,
            status=HealthStatus.UNAVAILABLE,
            details={"reason": "Mock adapter — service not connected", "mock": True},
            is_mock=True,
        )

    async def get_readiness(self) -> ServiceHealthResult:
        return await self.get_health()

    async def get_metrics(self) -> str:
        return f"# MOCK adapter for {self._service_name} — no metrics available\n"

    async def get_status(self) -> dict[str, Any]:
        result = (await self.get_health()).as_dict()
        result["is_mock"] = True
        return result
