from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InternalFeature:
    fe_id: str
    title: str | None = None
    raw: dict | None = None


class InternalSystemClient:
    """Adapter for the internal requirement system.

    Keep this file small and boring on purpose. In the internal network,
    replace the placeholder methods with real API calls.
    """

    def __init__(self, base_url: str | None = None, token: str | None = None) -> None:
        self.base_url = base_url
        self.token = token

    def get_feature(self, fe_id: str) -> InternalFeature:
        raise NotImplementedError("Implement internal API lookup by FE编号 in the internal network.")

    def add_comment(self, fe_id: str, comment: str) -> dict:
        raise NotImplementedError("Implement internal API comment creation in the internal network.")

    def get_requirement(self, rr_id: str) -> dict:
        raise NotImplementedError("Implement internal API lookup by RR编号 in the internal network.")

    def add_requirement_comment(self, rr_id: str, comment: str) -> dict:
        raise NotImplementedError("Implement internal API RR comment creation in the internal network.")


class DryRunInternalSystemClient(InternalSystemClient):
    """Safe client used by the MVP. It never writes to the real system."""

    def get_feature(self, fe_id: str) -> InternalFeature:
        return InternalFeature(fe_id=fe_id, title=None, raw={"mode": "dry_run"})

    def add_comment(self, fe_id: str, comment: str) -> dict:
        return {
            "mode": "dry_run",
            "fe_id": fe_id,
            "comment": comment,
            "message": "No internal API call was made.",
        }

    def get_requirement(self, rr_id: str) -> dict:
        return {"mode": "dry_run", "rr_id": rr_id}

    def add_requirement_comment(self, rr_id: str, comment: str) -> dict:
        return {
            "mode": "dry_run",
            "rr_id": rr_id,
            "comment": comment,
            "message": "No internal API call was made.",
        }
