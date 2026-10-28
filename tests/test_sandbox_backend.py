"""
Sandbox backend (T9.3): offline checks only. No network, no key.

A live run needs NEBIUS_API_KEY and NEBIUS_PROJECT_ID; until one completes, the sandbox
backend stays ASSUMED (see HANDOFF.md §2).
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ddp.compute import ComputeError, NebiusSandboxBackend, backend_from_name  # noqa: E402
from ddp.config import Settings  # noqa: E402


def test_refuses_without_project_id():
    with pytest.raises(ComputeError, match="NEBIUS_PROJECT_ID"):
        NebiusSandboxBackend(api_key="k").execute(b"print(1)", "{}")


def test_refuses_without_api_key():
    with pytest.raises(ComputeError, match="NEBIUS_API_KEY"):
        NebiusSandboxBackend(project_id="p").execute(b"print(1)", "{}")


def test_backend_from_name_passes_project_id():
    b = backend_from_name("nebius-sandbox", api_key="k", project_id="p")
    assert isinstance(b, NebiusSandboxBackend) and b.project_id == "p" and b.api_key == "k"


def test_settings_read_project_id_from_env(monkeypatch):
    monkeypatch.setenv("NEBIUS_PROJECT_ID", "project-xyz")
    assert Settings().nebius_project_id == "project-xyz"


class _FakeResult:
    def __init__(self, stdout="{}", exit_code=0, stderr="", uuid=None):
        self.stdout, self.exit_code, self.stderr, self.uuid = stdout, exit_code, stderr, uuid

    def wait(self):
        return self


def _install_fake_sdk(monkeypatch, result, op_id="op-123"):
    """A stand-in contree_sdk so the backend's control flow is testable offline."""
    class FakeImages:
        def use(self, name):
            return types.SimpleNamespace(run=lambda **kw: _Runner(result))

    class _Runner(_FakeResult):
        def __init__(self, r):
            self.__dict__.update(r.__dict__)
            self._r = r

        def wait(self):
            import asyncio
            asyncio.run(client._start_operation(object()))
            return self._r

    class FakeClient:
        def __init__(self, config=None):
            self.images = FakeImages()

        async def _start_operation(self, request):
            return op_id

    client = FakeClient()
    sdk = types.ModuleType("contree_sdk")
    sdk.ContreeSync = lambda config=None: client
    auth = types.ModuleType("contree_sdk.auth")
    auth.IAMAuth = lambda **kw: kw
    cfg = types.ModuleType("contree_sdk.config")
    cfg.ContreeConfig = lambda **kw: kw
    monkeypatch.setitem(sys.modules, "contree_sdk", sdk)
    monkeypatch.setitem(sys.modules, "contree_sdk.auth", auth)
    monkeypatch.setitem(sys.modules, "contree_sdk.config", cfg)


def test_run_reference_is_the_operation_uuid(monkeypatch):
    _install_fake_sdk(monkeypatch, _FakeResult(stdout='{"ok":1}'))
    out, ref = NebiusSandboxBackend("k", "p").execute(b"print(1)", "{}")
    assert out == '{"ok":1}' and ref == "op-123"


def test_nonzero_exit_is_a_compute_error(monkeypatch):
    _install_fake_sdk(monkeypatch, _FakeResult(exit_code=2, stderr="boom"))
    with pytest.raises(ComputeError, match="exit 2"):
        NebiusSandboxBackend("k", "p").execute(b"x", "{}")
