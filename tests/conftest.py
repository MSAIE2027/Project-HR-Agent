from __future__ import annotations

import os


def pytest_configure() -> None:
    # A developer's .env must not enable live OpenCode calls during the test suite.
    os.environ.pop("OPENCODE_API_KEY", None)
