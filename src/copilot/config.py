"""Shared constants: paths, dates and the lists of values used by filters."""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.environ.get("COPILOT_DB", REPO_ROOT / "data" / "synthetic" / "copilot.duckdb"))
KNOWLEDGE_DIR = REPO_ROOT / "knowledge"

DATA_START = date(2025, 1, 1)   # first booking date in the data
AS_OF = date(2026, 9, 30)       # last booking date = "data as-of" date

REGIONS = ["Europe", "Americas", "Africa & Middle East", "Asia-Pacific"]
TIERS = ["Small", "Mid", "Large", "Strategic"]
CONTRACT_TYPES = ["Standard", "Preferred", "Strategic"]
HAULS = ["short", "medium", "long"]
CABINS = ["Economy", "Premium Economy", "Business"]
STATUS_ORDER = ["On track", "At risk", "Off track"]


def index_dir() -> Path:
    """Where the vector index is stored (read at call time so tests can redirect it)."""
    return Path(os.environ.get("COPILOT_INDEX_DIR", REPO_ROOT / "data" / "index"))
