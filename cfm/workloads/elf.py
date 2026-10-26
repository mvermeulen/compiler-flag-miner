"""ELF helpers shared by the workload backends' compiled-flags audit and code
fingerprint (``audit_compiled_flags()``/``code_fingerprint()``). Each backend
decides which files to look at; these only read them.
"""

from __future__ import annotations

import hashlib
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable, Optional

_ELF_MAGIC = b"\x7fELF"
# e_type (offset 16, little-endian on every host this runs on): 2 = ET_EXEC,
# 3 = ET_DYN (PIE executables and shared libraries). 1 = ET_REL is an object file.
_LINKED_E_TYPES = {2, 3}


def is_elf(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            return path.is_file() and fh.read(4) == _ELF_MAGIC
    except OSError:
        return False


def is_linked_elf(path: Path) -> bool:
    """An ELF executable or shared library, not an object file."""
    try:
        with path.open("rb") as fh:
            header = fh.read(18)
    except OSError:
        return False
    return (
        path.is_file() and header[:4] == _ELF_MAGIC and len(header) == 18
        and int.from_bytes(header[16:18], "little") in _LINKED_E_TYPES
    )


def command_line_dump(paths: Iterable[Path]) -> Optional[str]:
    """Every file's ``readelf -p .GCC.command.line`` output, each preceded by
    ``# <filename>``. ``None`` when nothing could be read."""
    dumps = []
    for path in paths:
        try:
            proc = subprocess.run(
                ["readelf", "-p", ".GCC.command.line", str(path)],
                capture_output=True, text=True,
            )
        except OSError:
            continue
        if proc.returncode == 0:
            dumps.append(f"# {path.name}\n{proc.stdout}")
    return "\n".join(dumps) if dumps else None


def code_digest(paths: list[Path]) -> Optional[str]:
    """sha256 over the files with symbols, debug info, ``.GCC.command.line`` and
    the build ID stripped, so equal digests mean identical code. ``None`` when
    there's nothing to hash or ``objcopy`` fails."""
    if not paths:
        return None
    digest = hashlib.sha256()
    with tempfile.TemporaryDirectory(prefix="cfm-fingerprint-") as tmp:
        for path in paths:
            stripped = Path(tmp) / path.name
            try:
                proc = subprocess.run(
                    ["objcopy", "--strip-all", "--remove-section=.GCC.command.line",
                     "--remove-section=.note.gnu.build-id", str(path), str(stripped)],
                    capture_output=True, text=True,
                )
            except OSError:
                return None
            if proc.returncode != 0:
                return None
            digest.update(path.name.encode() + b"\0")
            with stripped.open("rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    digest.update(chunk)
    return digest.hexdigest()
