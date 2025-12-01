from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Dict, Any
from pathlib import Path

from .providers.blockstream import Tx, TxIO


@dataclass
class Dataset:
    root_address: str
    txs: List[Tx]

    def to_json(self) -> Dict[str, Any]:
        return {
            "address": self.root_address,
            "transactions": [
                {
                    "txid": t.txid,
                    "time": t.time,
                    "fee": t.fee_btc,
                    "vin": [{"addr": io.addr, "value": io.value_btc} for io in t.vin],
                    "vout": [{"addr": io.addr, "value": io.value_btc} for io in t.vout],
                }
                for t in self.txs
            ],
        }

    @staticmethod
    def from_json(obj: Dict[str, Any]) -> "Dataset":
        txs: List[Tx] = []
        for t in obj.get("transactions", []):
            vin = [TxIO(addr=x["addr"], value_btc=float(x["value"])) for x in t.get("vin", [])]
            vout = [TxIO(addr=x["addr"], value_btc=float(x["value"])) for x in t.get("vout", [])]
            txs.append(Tx(txid=t["txid"], time=int(t["time"]), vin=vin, vout=vout, fee_btc=float(t.get("fee", 0))))
        return Dataset(root_address=obj.get("address", "UNKNOWN"), txs=txs)

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_json(), ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def load(path: Path) -> "Dataset":
        return Dataset.from_json(json.loads(path.read_text(encoding="utf-8")))
