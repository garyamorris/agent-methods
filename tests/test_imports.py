"""Test suite verifying all agent architecture modules and patterns load correctly."""

import inspect
import pytest
from agent_methods.patterns import PATTERNS

def test_pattern_registry_completeness():
    """Verify all 10 patterns are registered with required metadata."""
    assert len(PATTERNS) == 10
    for key, p in PATTERNS.items():
        assert "id" in p
        assert "name" in p
        assert "description" in p
        assert "module" in p
        assert "topology" in p
        assert hasattr(p["module"], "run")
        assert inspect.iscoroutinefunction(p["module"].run)


@pytest.mark.parametrize("pattern_key", list(PATTERNS.keys()))
def test_pattern_docstring_exists(pattern_key):
    """Ensure every pattern has rich educational documentation in its module docstring."""
    p = PATTERNS[pattern_key]
    mod = p["module"]
    doc = mod.__doc__
    assert doc is not None
    assert len(doc) > 200
    assert "Architecture Overview" in doc
    assert "Communication Topology" in doc
    assert "When to Use" in doc


def test_deepseek_configuration():
    """Verify default model is deepseek-chat and base URL is configured."""
    from agent_methods.common import DEFAULT_MODEL, DEEPSEEK_BASE_URL
    assert DEFAULT_MODEL == "deepseek-chat"
    assert "api.deepseek.com" in DEEPSEEK_BASE_URL
