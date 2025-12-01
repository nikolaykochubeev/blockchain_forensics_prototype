from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional
from collections import Counter, defaultdict
from datetime import datetime, timezone

from .providers.blockstream import Tx


@dataclass
class AddressProfile:
    address: str
    tx_count_involving: int
    first_seen: Optional[int]
    last_seen: Optional[int]
    total_in_btc: float
    total_out_btc: float
    fees_paid_btc: float
    top_counterparties: List[Tuple[str, int]]
    hourly_activity: Dict[str, int]
    flags: List[str]


def _hour_bucket(ts: int) -> str:
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:00Z")


def build_address_profiles(txs: List[Tx]) -> Dict[str, AddressProfile]:
    involved = defaultdict(list)  # addr -> txids
    in_sum = Counter()
    out_sum = Counter()
    fees = Counter()
    first: Dict[str, int] = {}
    last: Dict[str, int] = {}
    cp = defaultdict(Counter)

    for tx in txs:
        ins = [(io.addr, io.value_btc) for io in tx.vin if io.addr != "UNKNOWN"]
        outs = [(io.addr, io.value_btc) for io in tx.vout if io.addr != "UNKNOWN"]
        addrs = {a for a, _ in ins} | {a for a, _ in outs}

        for a in addrs:
            involved[a].append(tx.txid)
            first[a] = min(first.get(a, tx.time), tx.time) if a in first else tx.time
            last[a] = max(last.get(a, tx.time), tx.time) if a in last else tx.time

        for a, v in ins:
            out_sum[a] += v
            fees[a] += tx.fee_btc / max(len(ins), 1)
            for b, _ in outs:
                if b != a:
                    cp[a][b] += 1

        for a, v in outs:
            in_sum[a] += v
            for b, _ in ins:
                if b != a:
                    cp[a][b] += 1

    profiles: Dict[str, AddressProfile] = {}
    for a, txids in involved.items():
        flags: List[str] = []
        if len(txids) >= 50:
            flags.append("high_tx_count")
        if float(in_sum[a]) > 10 and float(out_sum[a]) > 10:
            flags.append("high_volume")
        if first.get(a) and last.get(a) and (last[a] - first[a]) < 24 * 3600 and len(txids) >= 10:
            flags.append("burst_activity")

        buckets = Counter()
        for tx in txs:
            if any(io.addr == a for io in tx.vin) or any(io.addr == a for io in tx.vout):
                buckets[_hour_bucket(tx.time)] += 1

        profiles[a] = AddressProfile(
            address=a,
            tx_count_involving=len(txids),
            first_seen=first.get(a),
            last_seen=last.get(a),
            total_in_btc=float(in_sum[a]),
            total_out_btc=float(out_sum[a]),
            fees_paid_btc=float(fees[a]),
            top_counterparties=cp[a].most_common(10),
            hourly_activity=dict(buckets),
            flags=flags,
        )

    return profiles


def summarize_cluster(cluster: Set[str], profiles: Dict[str, AddressProfile]) -> Dict[str, object]:
    tx_count = sum(profiles[a].tx_count_involving for a in cluster if a in profiles)
    total_in = sum(profiles[a].total_in_btc for a in cluster if a in profiles)
    total_out = sum(profiles[a].total_out_btc for a in cluster if a in profiles)
    flags = sorted({f for a in cluster for f in (profiles[a].flags if a in profiles else [])})

    top_cp = Counter()
    for a in cluster:
        prof = profiles.get(a)
        if not prof:
            continue
        for b, c in prof.top_counterparties:
            top_cp[b] += c

    return {
        "size": len(cluster),
        "tx_count_involving": int(tx_count),
        "total_in_btc": float(total_in),
        "total_out_btc": float(total_out),
        "flags": flags,
        "top_counterparties": top_cp.most_common(10),
    }
