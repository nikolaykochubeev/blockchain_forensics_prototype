#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from src.providers.blockstream import BlockstreamProvider
from src.dataset import Dataset
from src.graph_build import build_graphs
from src.clustering import build_clusters
from src.profiling import build_address_profiles, summarize_cluster


# -----------------------------
# Standard pipeline
# -----------------------------

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


# -----------------------------
# CryptoDeepTools integration
# -----------------------------

def cmd_cdt_install(args: argparse.Namespace) -> None:
    repo_dir = Path(args.repo_dir)
    if repo_dir.exists():
        print(f"CryptoDeepTools already exists at {repo_dir}")
        return

    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call([
        "git", "clone",
        "https://github.com/demining/CryptoDeepTools.git",
        str(repo_dir)
    ])
    print(f"CryptoDeepTools cloned into {repo_dir}")


def cmd_cdt_pubtoaddr(args: argparse.Namespace) -> None:
    import json
    import tempfile
    from pathlib import Path
    import subprocess

    repo_dir = Path(args.repo_dir)
    script = repo_dir / "03CheckBitcoinAddressBalance" / "pubtoaddr.py"
    if not script.exists():
        raise FileNotFoundError(f"pubtoaddr.py not found at {script}")

    # Создаём временную рабочую директорию, куда положим pubkey.json
    with tempfile.TemporaryDirectory() as td:
        workdir = Path(td)

        # Записываем pubkey в формате, который ожидает скрипт (просто строка с переносом)
        (workdir / "pubkey.json").write_text(
            args.pubkey_hex + "\n",
            encoding="utf-8",
        )

        # Запускаем CDT-скрипт так, чтобы он видел pubkey.json
        # Используем абсолютный путь к скрипту
        result = subprocess.run(
            ["python", str(script.absolute())],
            cwd=str(workdir),
            capture_output=True,
            text=True
        )

        # Читаем результат из addresses.json
        addresses_file = workdir / "addresses.json"
        if addresses_file.exists():
            addresses = addresses_file.read_text(encoding="utf-8").strip()
            print(f"\nCryptoDeepTools pubtoaddr.py result:")
            print(f"Public Key: {args.pubkey_hex}")
            print(f"Bitcoin Address: {addresses}")
        else:
            print(f"Error: addresses.json not created")
            if result.stderr:
                print(f"Error output: {result.stderr}")


def cmd_extract_pubkey(args: argparse.Namespace) -> None:
    """Extract public key from a transaction input via Blockstream API"""
    import requests

    txid = args.txid
    vin_index = args.vin_index

    print(f"Fetching transaction {txid}...")
    url = f"https://blockstream.info/api/tx/{txid}"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        tx = response.json()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch transaction: {e}")

    if vin_index >= len(tx["vin"]):
        raise ValueError(f"Input index {vin_index} out of range (tx has {len(tx['vin'])} inputs)")

    vin = tx["vin"][vin_index]

    # Try to extract from witness data (SegWit)
    witness = vin.get("txinwitness") or []
    if witness:
        # Public key is typically the last element in witness
        pubkey = witness[-1]

        # Validate it looks like a public key (starts with 02, 03, or 04)
        if pubkey.startswith(('02', '03', '04')):
            print(f"\nExtracted public key from witness:")
            print(pubkey)
            return

    # Try legacy scriptsig
    scriptsig_asm = vin.get("scriptsig_asm", "")
    if scriptsig_asm:
        parts = scriptsig_asm.split()
        # Public key is typically the last element
        for part in reversed(parts):
            if part.startswith(('02', '03', '04')) and len(part) in [66, 130]:
                print(f"\nExtracted public key from scriptsig:")
                print(part)
                return

    raise RuntimeError(f"No public key found in input {vin_index} of transaction {txid}")


# -----------------------------
# CLI
# -----------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bf-prototype",
        description="Blockchain forensics prototype with CryptoDeepTools integration",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="Fetch address tx history via public API.")
    f.add_argument("address")
    f.add_argument("--limit", type=int, default=200)
    f.add_argument("--base-url", default="https://blockstream.info/api")
    f.add_argument("--out", default="dataset.json")
    f.set_defaults(func=cmd_fetch)

    a = sub.add_parser("analyze", help="Analyze dataset JSON.")
    a.add_argument("dataset")
    a.add_argument("--max-clusters", type=int, default=20)
    a.add_argument("--out", default="analysis.json")
    a.set_defaults(func=cmd_analyze)

    c1 = sub.add_parser("cdt-install", help="Clone CryptoDeepTools repository.")
    c1.add_argument("--repo-dir", default="vendor/CryptoDeepTools")
    c1.set_defaults(func=cmd_cdt_install)

    c2 = sub.add_parser("cdt-pubtoaddr", help="Run CryptoDeepTools pubtoaddr.py.")
    c2.add_argument("pubkey_hex")
    c2.add_argument("--repo-dir", default="vendor/CryptoDeepTools")
    c2.set_defaults(func=cmd_cdt_pubtoaddr)

    e = sub.add_parser("extract-pubkey", help="Extract pubkey from a real txid via Blockstream API.")
    e.add_argument("txid")
    e.add_argument("--vin-index", type=int, default=0)
    e.set_defaults(func=cmd_extract_pubkey)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
