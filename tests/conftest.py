import pytest


@pytest.fixture(autouse=True)
def local_account_mode_for_tests(monkeypatch):
    # Existing account unit tests deliberately exercise the isolated SQLite dev adapter.
    monkeypatch.setenv("PREDICTAI_ACCOUNT_MODE", "local")
