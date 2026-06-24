import pytest
import yaml

from settings_manager import Settings, SettingsValidationError


def test_localization_czech(tmp_settings_dir, base_schema):
    # Invalid config to trigger validation error
    config_file = tmp_settings_dir / "config.yaml"
    with config_file.open("w") as f:
        yaml.dump({"app": {"port": "wrong"}}, f)

    with pytest.raises(SettingsValidationError) as excinfo:
        Settings(schema=base_schema, settings_dir=tmp_settings_dir, language="cs")

    # Check if the error message is translated
    error_msg = str(excinfo.value).lower()
    assert "validace" in error_msg or "selha" in error_msg


def test_localization_fallback(tmp_settings_dir, base_schema):
    config_file = tmp_settings_dir / "config.yaml"
    with config_file.open("w") as f:
        yaml.dump({"app": {"port": "wrong"}}, f)

    # Non-existent language should fallback to English
    with pytest.raises(SettingsValidationError) as excinfo:
        Settings(schema=base_schema, settings_dir=tmp_settings_dir, language="nonexistent")

    assert "failed" in str(excinfo.value).lower() or "invalid" in str(excinfo.value).lower()
