import pytest

from settings_manager import Settings


@pytest.fixture(autouse=True)
def reset_settings():
    """Reset the Settings singleton before each test."""
    Settings.reset()
    yield
    Settings.reset()


@pytest.fixture
def tmp_settings_dir(tmp_path):
    """Provide a temporary directory for settings files."""
    settings_dir = tmp_path / ".settings"
    settings_dir.mkdir()
    return settings_dir


@pytest.fixture
def base_schema():
    """Provide a base validation schema."""
    return {
        "app": {
            "type": "dict",
            "schema": {
                "name": {"type": "string", "required": True},
                "port": {"type": "integer", "default": 8080},
            },
        },
        "database": {
            "type": "dict",
            "schema": {
                "host": {"type": "string", "required": True},
                "timeout": {"type": "integer"},
            },
        },
    }
