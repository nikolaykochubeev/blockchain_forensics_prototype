from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


CRYPTODEEPTOOLS_GIT = "https://github.com/demining/CryptoDeepTools.git"


@dataclass(frozen=True)
class CryptoDeepToolsPaths:
    root: Path
    pubtoaddr: Path
    checker: Path


class CryptoDeepToolsBridge:
    """
    Safe integration layer for the public repository CryptoDeepTools.

    We DO NOT execute or wrap modules intended for private-key recovery, wallet cracking,
    or exploitation. This bridge only supports:
      - installing (cloning) the repo for reproducibility
      - using the public 'pubtoaddr.py' converter (PUBKEY HEX -> Base58 address)

    Reference: CryptoDeepTools repository contains a folder '03CheckBitcoinAddressBalance'
    with scripts 'pubtoaddr.py' and 'bitcoin-checker.py'. Use is limited to 'pubtoaddr.py'.
    """

    def __init__(self, repo_dir: Path):
        self.repo_dir = repo_dir

    def ensure_installed(self) -> None:
        if (self.repo_dir / ".git").exists():
            return
        self.repo_dir.parent.mkdir(parents=True, exist_ok=True)
        subprocess.check_call(["git", "clone", "--depth", "1", CRYPTODEEPTOOLS_GIT, str(self.repo_dir)])

    def paths(self) -> CryptoDeepToolsPaths:
        pubtoaddr = self.repo_dir / "03CheckBitcoinAddressBalance" / "pubtoaddr.py"
        checker = self.repo_dir / "03CheckBitcoinAddressBalance" / "bitcoin-checker.py"
        if not pubtoaddr.exists():
            raise FileNotFoundError(f"CryptoDeepTools pubtoaddr.py not found at: {pubtoaddr}")
        # checker may exist, but we don't use it in this prototype
        return CryptoDeepToolsPaths(root=self.repo_dir, pubtoaddr=pubtoaddr, checker=checker)

    def pubkey_hex_to_base58(self, pubkey_hex: str, python: str = "python3") -> str:
        """
        Convert Bitcoin public key (hex) to Base58 address by invoking CryptoDeepTools/pubtoaddr.py.

        Implementation detail:
        CryptoDeepTools/pubtoaddr.py reads file 'pubkey.json' and writes 'addresses.json'.
        We run it inside a temporary directory to avoid polluting the project directory.
        """
        pubkey_hex = pubkey_hex.strip().lower().replace("0x", "")
        if not all(c in "0123456789abcdef" for c in pubkey_hex) or len(pubkey_hex) < 66:
            raise ValueError("pubkey_hex must be a hex-encoded public key (uncompressed ~130 hex or compressed ~66 hex)")

        self.ensure_installed()
        p = self.paths()

        with tempfile.TemporaryDirectory(prefix="bf_cdt_") as td:
            td_path = Path(td)
            (td_path / "pubkey.json").write_text(pubkey_hex + "\n", encoding="utf-8")

            # Run the script. It expects to work in its CWD.
            # We copy the script into tempdir to keep relative file IO simple.
            local_script = td_path / "pubtoaddr.py"
            local_script.write_text(p.pubtoaddr.read_text(encoding="utf-8"), encoding="utf-8")

            subprocess.check_call([python, str(local_script)], cwd=str(td_path))

            out_file = td_path / "addresses.json"
            if not out_file.exists():
                raise RuntimeError("CryptoDeepTools pubtoaddr.py did not produce addresses.json")
            addr = out_file.read_text(encoding="utf-8").strip().splitlines()[0].strip()
            if not addr:
                raise RuntimeError("addresses.json is empty")
            return addr
