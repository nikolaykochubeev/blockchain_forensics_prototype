#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.providers.blockstream import BlockstreamProvider
from src.dataset import Dataset
from src.graph_build import build_graphs
from src.clustering import build_clusters
from src.profiling import build_address_profiles, summarize_cluster
from src.osint import OsintLabelStore, enrich_addresses


def cmd_fetch(args: argparse.Namespace) -> None:
    provider = BlockstreamProvider(base_url=args.base_url)
    txs = provider.fetch_address_txs(args.address, limit=args.limit)
    ds = Dataset(root_address=args.address, txs=txs)
    ds.save(Path(args.out))
    print(f"Saved dataset to {args.out} (txs={len(txs)})")


def cmd_analyze(args: argparse.Namespace) -> None:
    ds = Dataset.load(Path(args.dataset))
    graphs = build_graphs(ds.txs)
    clusters = build_clusters(ds.txs)
    profiles = build_address_profiles(ds.txs)

    store = OsintLabelStore()
    if args.labels:
        store.load_json(Path(args.labels))

    all_addrs = set(profiles.keys())
    labels = enrich_addresses(all_addrs, store)

    cluster_summaries = []
    for i, c in enumerate(clusters.clusters[: args.max_clusters]):
        cluster_summaries.append(
            {"cluster_id": i, "addresses": sorted(c), "summary": summarize_cluster(c, profiles)}
        )

    out = {
        "root_address": ds.root_address,
        "tx_count": len(ds.txs),
        "notes": clusters.notes,
        "clusters": cluster_summaries,
        "labels": labels,
        "address_profiles": {
            a: {
                "tx_count_involving": p.tx_count_involving,
                "first_seen": p.first_seen,
                "last_seen": p.last_seen,
                "total_in_btc": p.total_in_btc,
                "total_out_btc": p.total_out_btc,
                "fees_paid_btc": p.fees_paid_btc,
                "top_counterparties": p.top_counterparties,
                "flags": p.flags,
            }
            for a, p in profiles.items()
        },
        "graph_stats": {
            "address_graph_nodes": graphs.address_graph.number_of_nodes(),
            "address_graph_edges": graphs.address_graph.number_of_edges(),
            "bipartite_nodes": graphs.bipartite_graph.number_of_nodes(),
            "bipartite_edges": graphs.bipartite_graph.number_of_edges(),
        },
    }

    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved analysis to {args.out}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bf-prototype",
        description="Educational Bitcoin profiling pipeline (open tools, public data only).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="Fetch address tx history via public API and store dataset JSON.")
    f.add_argument("address", help="Bitcoin address (base58 or bech32).")
    f.add_argument("--limit", type=int, default=200, help="Max transactions to fetch.")
    f.add_argument("--base-url", default="https://blockstream.info/api", help="Esplora API base URL.")
    f.add_argument("--out", default="dataset.json", help="Output dataset JSON path.")
    f.set_defaults(func=cmd_fetch)

    a = sub.add_parser("analyze", help="Run graph + clustering + profiling pipeline on dataset JSON.")
    a.add_argument("dataset", help="Path to dataset JSON.")
    a.add_argument("--labels", default=None, help="Optional JSON with OSINT labels {address:{kind,name,source}}.")
    a.add_argument("--max-clusters", type=int, default=20, help="How many clusters to include in report.")
    a.add_argument("--out", default="analysis.json", help="Output analysis JSON path.")
    a.set_defaults(func=cmd_analyze)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
