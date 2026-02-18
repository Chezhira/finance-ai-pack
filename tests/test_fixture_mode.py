from finance_ai_pack.config import Settings


def test_fixture_mode_default_from_env(monkeypatch):
    monkeypatch.delenv("FIXTURE_MODE", raising=False)
    settings = Settings.from_env()
    assert settings.fixture_mode is True


def test_odoo_username_prefers_new_env_var(monkeypatch):
    monkeypatch.setenv("ODOO_USERNAME", "alice")
    monkeypatch.setenv("ODOO_USER", "bob")
    settings = Settings.from_env()
    assert settings.odoo_username == "alice"
