"""Pytest hooks: ensure required env exists before `app` modules import `Settings`."""

from __future__ import annotations

import os

# `llm_api_key` is required; tests must not depend on a developer .env file.
os.environ.setdefault("LLM_API_KEY", "test-openai-key-not-used-in-unit-tests")
