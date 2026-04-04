from app.utils.config import Settings


def test_resolved_chrome_path_prefers_path_lookup(monkeypatch) -> None:
    def fake_which(name: str) -> str | None:
        if name == "google-chrome":
            return "/usr/bin/google-chrome"
        return None

    monkeypatch.setattr("app.utils.config.shutil.which", fake_which)

    settings = Settings(CHROME_PATH="/path/to/chrome-headless-shell")

    assert settings.resolved_chrome_path == "/usr/bin/google-chrome"


def test_resolved_marp_cli_path_uses_configured_value() -> None:
    settings = Settings(MARP_CLI_PATH="/custom/bin/marp")

    assert settings.resolved_marp_cli_path == "/custom/bin/marp"
