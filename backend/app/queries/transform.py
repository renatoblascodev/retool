"""Restricted JavaScript-like transform sandbox using RestrictedPython.

Provides a safe way for users to write simple data transformation scripts
that run on query results without access to the filesystem, network, or
dangerous builtins.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

logger = logging.getLogger(__name__)

_TRANSFORM_TIMEOUT_SECONDS = 2

# Check availability at import time
try:
    from RestrictedPython import compile_restricted, safe_builtins, safe_globals  # noqa: F401
    from RestrictedPython.Guards import (  # noqa: F401
        guarded_iter_unpack_sequence,
        guarded_unpack_sequence,
    )
    _RESTRICTED_PYTHON_AVAILABLE = True
except ImportError:
    _RESTRICTED_PYTHON_AVAILABLE = False

# Extended builtins made available inside transform scripts.
# These supplement RestrictedPython's safe_builtins (which is very sparse).
_EXTRA_BUILTINS: dict[str, Any] = {
    # types
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "set": set,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "bytes": bytes,
    # iteration / functional
    "sorted": sorted,
    "filter": filter,
    "map": map,
    "zip": zip,
    "enumerate": enumerate,
    "range": range,
    "reversed": reversed,
    # math / comparison
    "sum": sum,
    "min": min,
    "max": max,
    "abs": abs,
    "round": round,
    # predicates
    "any": any,
    "all": all,
    "isinstance": isinstance,
    "len": len,
}


def _run_in_sandbox(script: str, data: Any) -> Any:
    """
    Execute a transform script synchronously inside RestrictedPython.

    The script receives `data` as a local variable and should assign the
    result to the `result` variable.

    Returns the transformed value.
    Raises ValueError for script errors.
    """
    if not _RESTRICTED_PYTHON_AVAILABLE:
        raise RuntimeError(
            "RestrictedPython is not installed. Add 'RestrictedPython' to requirements.txt."
        )

    from RestrictedPython import compile_restricted, safe_builtins, safe_globals  # noqa: PLC0415
    from RestrictedPython.Guards import (  # noqa: PLC0415
        guarded_iter_unpack_sequence,
        guarded_unpack_sequence,
    )

    # Compile with RestrictedPython — raises SyntaxError if invalid
    try:
        byte_code = compile_restricted(script, filename="<transform>", mode="exec")
    except SyntaxError as exc:
        raise ValueError(f"Syntax error in transform script: {exc}") from exc

    # Build globals: safe_globals provides _getiter_, _write_ guards etc.
    glb: dict[str, Any] = dict(safe_globals)
    # Extend safe_builtins with our extra types/functions
    builtins: dict[str, Any] = dict(safe_builtins)
    builtins.update(_EXTRA_BUILTINS)
    glb["__builtins__"] = builtins
    # Subscript guard: data['key'] and data[0] require _getitem_
    glb["_getitem_"] = lambda obj, key: obj[key]
    glb["_getiter_"] = iter
    glb["_iter_unpack_sequence_"] = guarded_iter_unpack_sequence
    glb["_unpack_sequence_"] = guarded_unpack_sequence

    lcl: dict[str, Any] = {"data": data, "result": data}

    try:
        exec(byte_code, glb, lcl)  # noqa: S102 — controlled sandbox execution
    except Exception as exc:
        # Catch any runtime errors from the script
        raise ValueError(f"Transform error: {exc}") from exc

    return lcl.get("result", data)


def run_transform(script: str | None, data: Any) -> Any:
    """
    Run a user-provided transform script with a hard timeout.

    Args:
        script: Python script string. Should assign to `result`.
                Empty/None scripts return data unchanged.
        data: The query result to transform (list or dict).

    Returns:
        The transformed data.

    Raises:
        ValueError: If the script has a syntax or runtime error.
        TimeoutError: If the script exceeds the timeout.
    """
    if not script or not script.strip():
        return data

    result_container: dict[str, Any] = {}
    exc_container: dict[str, Any] = {}

    def _run() -> None:
        try:
            result_container["r"] = _run_in_sandbox(script, data)
        except Exception as exc:  # noqa: BLE001
            exc_container["e"] = exc

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=_TRANSFORM_TIMEOUT_SECONDS)
    if t.is_alive():
        raise TimeoutError("Transform script exceeded time limit")
    if "e" in exc_container:
        raise exc_container["e"]
    return result_container.get("r", data)
