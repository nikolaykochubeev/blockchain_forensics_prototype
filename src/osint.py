from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Set
from pathlib import Path
import json


@dataclass
class Label:
    kind: str   # exchange/mixer/service/other
    name: str
    source: str


class OsintLabelStore:
    # Offline label store (JSON). Extend with open datasets as needed.

    def __init__(self, labels: Optional[Dict[str, Label]] = None):
        self.labels: Dict[str, Label] = labels or {}

    def get(self, address: str) -> Optional[Label]:
        return self.labels.get(address)

    def add(self, address: str, kind: str, name: str, source: str) -> None:
        self.labels[address] = Label(kind=kind, name=name, source=source)

    def load_json(self, path: Path) -> None:
        obj = json.loads(path.read_text(encoding="utf-8"))
        for addr, it in obj.items():
            self.add(addr, it["kind"], it["name"], it.get("source", str(path)))

    def save_json(self, path: Path) -> None:
        path.write_text(
            json.dumps({a: l.__dict__ for a, l in self.labels.items()}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def enrich_addresses(addresses: Set[str], store: OsintLabelStore) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for a in addresses:
        lab = store.get(a)
        if lab:
            out[a] = {"kind": lab.kind, "name": lab.name, "source": lab.source}
    return out
