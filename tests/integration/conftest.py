"""Integration tests call Gemini (and sometimes a deployed agent). Opt in with RUN_INTEGRATION=1."""

import os

import pytest


def pytest_collection_modifyitems(config, items):
    if os.environ.get("RUN_INTEGRATION") != "1":
        skip = pytest.mark.skip(reason="set RUN_INTEGRATION=1 to call Gemini")
        for item in items:
            if "integration" in item.path.parts:
                item.add_marker(skip)
