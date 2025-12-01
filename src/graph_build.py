from __future__ import annotations

from dataclasses import dataclass
from typing import List
import networkx as nx

from .providers.blockstream import Tx


@dataclass
class GraphArtifacts:
    address_graph: nx.DiGraph
    bipartite_graph: nx.Graph


def build_graphs(txs: List[Tx]) -> GraphArtifacts:
    # 1) address_graph: directed weighted graph address -> address by value
    # 2) bipartite_graph: undirected graph with nodes ('a', addr) and ('t', txid)
    g_addr = nx.DiGraph()
    g_bi = nx.Graph()

    for tx in txs:
        tx_node = ("t", tx.txid)
        g_bi.add_node(tx_node, kind="tx", time=tx.time)

        vin_addrs = [(io.addr, io.value_btc) for io in tx.vin if io.addr != "UNKNOWN"]
        vout_addrs = [(io.addr, io.value_btc) for io in tx.vout if io.addr != "UNKNOWN"]

        for a, v in vin_addrs:
            an = ("a", a)
            g_bi.add_node(an, kind="addr")
            g_bi.add_edge(an, tx_node, role="vin", value=v)

        for a, v in vout_addrs:
            an = ("a", a)
            g_bi.add_node(an, kind="addr")
            g_bi.add_edge(tx_node, an, role="vout", value=v)

        in_sum = sum(v for _, v in vin_addrs) or 0.0
        if in_sum <= 0:
            continue

        for in_addr, in_val in vin_addrs:
            for out_addr, out_val in vout_addrs:
                w = (in_val / in_sum) * out_val
                if g_addr.has_edge(in_addr, out_addr):
                    g_addr[in_addr][out_addr]["value"] += w
                    g_addr[in_addr][out_addr]["tx_count"] += 1
                else:
                    g_addr.add_edge(in_addr, out_addr, value=w, tx_count=1, last_time=tx.time)
                g_addr[in_addr][out_addr]["last_time"] = max(g_addr[in_addr][out_addr]["last_time"], tx.time)

    return GraphArtifacts(address_graph=g_addr, bipartite_graph=g_bi)
