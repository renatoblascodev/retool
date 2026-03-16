"""Tests for the JS transform sandbox (RestrictedPython)."""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Import guard — skip tests gracefully if RestrictedPython not installed
# ---------------------------------------------------------------------------
try:
    from RestrictedPython import compile_restricted  # noqa: F401
    from app.queries.transform import run_transform  # noqa: PLC0415
    _RESTRICTED_PYTHON_AVAILABLE = True
except ImportError:
    _RESTRICTED_PYTHON_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not _RESTRICTED_PYTHON_AVAILABLE,
    reason="RestrictedPython not installed",
)


# ---------------------------------------------------------------------------
# Basic functionality
# ---------------------------------------------------------------------------


def test_transform_empty_script_returns_data():
    """Empty/None script returns data unchanged."""
    data = [{"id": 1}, {"id": 2}]
    assert run_transform("", data) == data
    assert run_transform(None, data) == data  # type: ignore[arg-type]


def test_transform_filter_list():
    """Script can filter a list by assigning to result."""
    data = [{"active": True, "id": 1}, {"active": False, "id": 2}, {"active": True, "id": 3}]
    script = "result = [row for row in data if row['active']]"
    out = run_transform(script, data)
    assert isinstance(out, list)
    assert len(out) == 2
    assert all(r["active"] for r in out)


def test_transform_sort_list():
    """Script can sort a list."""
    data = [{"name": "Bob"}, {"name": "Alice"}, {"name": "Charlie"}]
    script = "result = sorted(data, key=lambda r: r['name'])"
    out = run_transform(script, data)
    assert out[0]["name"] == "Alice"
    assert out[1]["name"] == "Bob"


def test_transform_slice():
    """Script can slice a list."""
    data = list(range(10))
    script = "result = data[:3]"
    out = run_transform(script, data)
    assert out == [0, 1, 2]  # list returned directly (not wrapped)


def test_transform_dict_input():
    """Script works with dict input."""
    data = {"users": [{"id": 1}, {"id": 2}], "total": 2}
    script = "result = data['users']"
    out = run_transform(script, data)
    assert isinstance(out, list)
    assert len(out) == 2


def test_transform_map():
    """Script can use map() to transform fields."""
    data = [{"name": "alice"}, {"name": "bob"}]
    script = "result = list(map(lambda r: {'name': r['name'].upper() if isinstance(r['name'], str) else r['name']}, data))"
    out = run_transform(script, data)
    assert out[0]["name"] == "ALICE"


# ---------------------------------------------------------------------------
# Security — import and eval blocking
# ---------------------------------------------------------------------------


def test_transform_import_blocked():
    """Importing modules should raise ValueError (blocked by RestrictedPython)."""
    script = "import os; result = os.getcwd()"
    with pytest.raises(ValueError, match="(?i)(import|restricted|not allowed|error)"):
        run_transform(script, [])


def test_transform_exec_blocked():
    """Using exec inside script should be blocked."""
    script = "exec('import os')"
    with pytest.raises((ValueError, NameError)):
        run_transform(script, [])


def test_transform_open_blocked():
    """File open should not be available."""
    script = "result = open('/etc/passwd').read()"
    with pytest.raises((ValueError, NameError, AttributeError)):
        run_transform(script, [])


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def test_transform_syntax_error():
    """Syntax errors in script raise ValueError."""
    script = "result = [x for x in"  # incomplete
    with pytest.raises(ValueError, match="(?i)syntax"):
        run_transform(script, [])


def test_transform_runtime_exception():
    """Runtime errors in script raise ValueError."""
    script = "result = data['nonexistent_key']"  # KeyError on list input
    with pytest.raises(ValueError, match="(?i)transform error"):
        run_transform(script, [{"id": 1}])


def test_transform_timeout():
    """Scripts that run too long should raise TimeoutError."""
    # Infinite loop — should time out
    script = "result = []\nwhile True:\n    result.append(1)"
    with pytest.raises(TimeoutError):
        run_transform(script, [])
