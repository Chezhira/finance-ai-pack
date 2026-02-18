from finance_ai_pack.config import Settings


def test_fixture_mode_default_from_env(monkeypatch):
    monkeypatch.delenv("FIXTURE_MODE", raising=False)
    settings = Settings.from_env()
    assert settings.fixture_mode is True
