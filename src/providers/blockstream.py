from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Iterable
import requests


@dataclass(frozen=True)
class TxIO:
    addr: str
    value_btc: float


@dataclass(frozen=True)
class Tx:
    txid: str
    time: int  # unix epoch seconds
    vin: List[TxIO]
    vout: List[TxIO]
    fee_btc: float


class BlockstreamProvider:
    # Data provider based on Blockstream's public Esplora API (https://blockstream.info/api).
    # The API is rate-limited; a simple exponential backoff is implemented.

    def __init__(self, base_url: str = "https://blockstream.info/api", session: Optional[requests.Session] = None):
        self.base_url = base_url.rstrip("/")
        self.s = session or requests.Session()

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None, retries: int = 5) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        delay = 0.7
        last_err: Optional[Exception] = None
        for _ in range(retries):
            try:
                r = self.s.get(url, params=params, timeout=30)
                if r.status_code == 429:
                    time.sleep(delay)
                    delay = min(delay * 1.8, 10)
                    continue
                r.raise_for_status()
                return r.json()
            except Exception as e:
                last_err = e
                time.sleep(delay)
                delay = min(delay * 1.8, 10)
        raise RuntimeError(f"Blockstream request failed: {url}") from last_err

    def iter_address_txs(self, address: str, limit: int = 250) -> Iterable[Dict[str, Any]]:
        # Pagination: /address/:address/txs and /address/:address/txs/chain/:last_seen_txid
        seen = 0
        batch = self._get(f"address/{address}/txs")
        while batch:
            for tx in batch:
                yield tx
                seen += 1
                if seen >= limit:
                    return
            last = batch[-1]["txid"]
            batch = self._get(f"address/{address}/txs/chain/{last}")

    @staticmethod
    def _sat_to_btc(sats: int) -> float:
        return sats / 100_000_000

    def normalize_tx(self, tx: Dict[str, Any]) -> Tx:
        t = tx.get("status", {}).get("block_time") or int(time.time())
        vin: List[TxIO] = []
        for inp in tx.get("vin", []):
            prev = inp.get("prevout") or {}
            addr = prev.get("scriptpubkey_address") or "UNKNOWN"
            val = self._sat_to_btc(prev.get("value", 0))
            vin.append(TxIO(addr=addr, value_btc=val))

        vout: List[TxIO] = []
        for outp in tx.get("vout", []):
            addr = outp.get("scriptpubkey_address") or "UNKNOWN"
            val = self._sat_to_btc(outp.get("value", 0))
            vout.append(TxIO(addr=addr, value_btc=val))

        fee = self._sat_to_btc(int(tx.get("fee", 0)))
        return Tx(txid=tx["txid"], time=int(t), vin=vin, vout=vout, fee_btc=fee)

    def fetch_address_txs(self, address: str, limit: int = 250) -> List[Tx]:
        txs: List[Tx] = []
        for raw in self.iter_address_txs(address, limit=limit):
            txs.append(self.normalize_tx(raw))
        return txs
