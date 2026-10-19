"""Who can see what. One place, used by the dashboards now and by the assistant later.

Three roles (see knowledge/00_overview.md):
- global_analyst:    everything
- regional_director: only the accounts of one sales region, and that region's targets
- account_manager:   only the accounts they manage; no regional targets (they aggregate
                     accounts the manager does not own)

The scope is turned into a SQL condition that is ALWAYS added to the query, so a user
cannot widen it by choosing a filter.
"""
from __future__ import annotations

from dataclasses import dataclass

ROLE_GLOBAL = "global_analyst"
ROLE_REGIONAL = "regional_director"
ROLE_MANAGER = "account_manager"
ROLES = (ROLE_GLOBAL, ROLE_REGIONAL, ROLE_MANAGER)
ROLE_LABELS = {ROLE_GLOBAL: "Global analyst", ROLE_REGIONAL: "Regional director",
               ROLE_MANAGER: "Account manager"}


@dataclass(frozen=True)
class Scope:
    role: str = ROLE_GLOBAL
    region: str | None = None
    manager: str | None = None

    def __post_init__(self) -> None:
        if self.role not in ROLES:
            raise ValueError(f"Unknown role: {self.role}")
        if self.role == ROLE_REGIONAL and not self.region:
            raise ValueError("A regional director needs a region")
        if self.role == ROLE_MANAGER and not self.manager:
            raise ValueError("An account manager needs a manager name")

    def account_predicate(self, alias: str = "a") -> tuple[str, list[str]]:
        """SQL condition on the accounts table (alias given) and its parameters."""
        if self.role == ROLE_REGIONAL:
            return f"{alias}.sales_region = ?", [self.region]
        if self.role == ROLE_MANAGER:
            return f"{alias}.account_manager = ?", [self.manager]
        return "TRUE", []

    @property
    def can_view_targets(self) -> bool:
        return self.role != ROLE_MANAGER

    def target_predicate(self, alias: str = "t") -> tuple[str, list[str]]:
        """SQL condition on the targets table. Account managers get no targets at all."""
        if not self.can_view_targets:
            raise PermissionError("Regional targets are not available to account managers")
        if self.role == ROLE_REGIONAL:
            return f"{alias}.sales_region = ?", [self.region]
        return "TRUE", []

    @property
    def key(self) -> str:
        """Short text identifying the scope (used to reset filter widgets when it changes)."""
        return f"{self.role}:{self.region or ''}:{self.manager or ''}"

    def describe(self) -> str:
        if self.role == ROLE_REGIONAL:
            return f"Regional director, {self.region} (only the accounts of this region)"
        if self.role == ROLE_MANAGER:
            return f"Account manager, {self.manager} (only your own accounts)"
        return "Global analyst (all regions and accounts)"


GLOBAL = Scope()
