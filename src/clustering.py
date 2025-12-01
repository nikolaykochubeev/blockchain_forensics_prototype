from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set, Optional

from .providers.blockstream import Tx


@dataclass
class ClusteringResult:
    clusters: List[Set[str]]
    addr_to_cluster: Dict[str, int]
    notes: List[str]


def _union_find():
    parent: Dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    def groups() -> List[Set[str]]:
        out: Dict[str, Set[str]] = {}
        for x in list(parent.keys()):
            r = find(x)
            out.setdefault(r, set()).add(x)
        return list(out.values())

    return union, groups


def cluster_multi_input(txs: List[Tx], min_inputs: int = 2) -> List[Set[str]]:
    # Multi-input heuristic: inputs used together likely controlled by the same entity.
    union, groups = _union_find()
    for tx in txs:
        ins = [io.addr for io in tx.vin if io.addr != "UNKNOWN"]
        if len(ins) < min_inputs:
            continue
        base = ins[0]
        for a in ins[1:]:
            union(base, a)
    return groups()


def detect_change_address(tx: Tx) -> Optional[str]:
    # Conservative change heuristic:
    # - exactly one output address is not among inputs (common in simple spends)
    in_addrs = {io.addr for io in tx.vin if io.addr != "UNKNOWN"}
    outs = [io.addr for io in tx.vout if io.addr != "UNKNOWN"]
    if len(set(outs)) != len(outs):  # repeated outputs -> skip
        return None
    candidates = [a for a in outs if a not in in_addrs]
    return candidates[0] if len(candidates) == 1 else None


def build_clusters(txs: List[Tx]) -> ClusteringResult:
    notes: List[str] = []
    clusters = cluster_multi_input(txs)
    addr_to_cluster: Dict[str, int] = {}

    for i, c in enumerate(clusters):
        for a in c:
            addr_to_cluster[a] = i

    notes.append(f"Multi-input clusters computed: {len(clusters)}")

    linked = 0
    for tx in txs:
        ch = detect_change_address(tx)
        if not ch:
            continue
        ins = [io.addr for io in tx.vin if io.addr != "UNKNOWN"]
        if not ins:
            continue
        root = ins[0]
        if root in addr_to_cluster:
            clusters[addr_to_cluster[root]].add(ch)
            addr_to_cluster[ch] = addr_to_cluster[root]
            linked += 1

    notes.append(f"Change-address linked: {linked}")

    # normalize
    norm: Dict[int, Set[str]] = {}
    for a, i in addr_to_cluster.items():
        norm.setdefault(i, set()).add(a)
    clusters = list(norm.values())
    addr_to_cluster = {a: i for i, c in enumerate(clusters) for a in c}

    return ClusteringResult(clusters=clusters, addr_to_cluster=addr_to_cluster, notes=notes)
