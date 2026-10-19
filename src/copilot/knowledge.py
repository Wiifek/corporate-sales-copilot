"""Read the knowledge documents (used to show metric definitions as tooltips)."""
from __future__ import annotations

import re
from functools import lru_cache

from copilot.config import KNOWLEDGE_DIR


def sql_blocks(text: str) -> list[str]:
    return re.findall(r"```sql\n(.*?)```", text, flags=re.S)


@lru_cache(maxsize=1)
def glossary_metrics() -> dict[str, str]:
    """Return {metric name: full text of its section} from the '## Metrics' part."""
    section, current, metrics = None, None, {}
    for line in (KNOWLEDGE_DIR / "metrics_glossary.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section, current = line[3:].strip(), None
        elif line.startswith("### "):
            current = line[4:].strip()
            if section == "Metrics":
                metrics[current] = ""
        elif section == "Metrics" and current:
            metrics[current] += line + "\n"
    return metrics


@lru_cache(maxsize=1)
def metric_definitions() -> dict[str, str]:
    """Return {metric name: one-line English definition}."""
    out = {}
    for name, body in glossary_metrics().items():
        m = re.search(r"\*\*Definition:\*\* (.+)", body)
        out[name] = m.group(1).strip() if m else ""
    return out
