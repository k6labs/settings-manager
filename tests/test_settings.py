import pytest
import tomli_w
import yaml

from settings_manager import Settings, SettingsValidationError


def test_loading_yaml(tmp_settings_dir, base_schema):
    config_file = tmp_settings_dir / "config.yaml"
    data = {"app": {"name": "Test App", "port": 9000}}
    with config_file.open("w") as f:
        yaml.dump(data, f)

    settings = Settings(schema=base_schema, settings_dir=tmp_settings_dir)
    assert settings["app"]["name"] == "Test App"
    assert settings["app"]["port"] == 9000


def test_loading_toml(tmp_settings_dir, base_schema):
    config_file = tmp_settings_dir / "config.toml"
    data = {"database": {"host": "localhost", "timeout": 30}}
    with config_file.open("wb") as f:
        tomli_w.dump(data, f)

    # We also need a name for 'app' to pass validation if required
    app_file = tmp_settings_dir / "app.yaml"
    with app_file.open("w") as f:
        yaml.dump({"app": {"name": "App"}}, f)

    settings = Settings(schema=base_schema, settings_dir=tmp_settings_dir)
    assert settings["database"]["host"] == "localhost"
    assert settings["database"]["timeout"] == 30


def test_deep_merge(tmp_settings_dir, base_schema):
    file1 = tmp_settings_dir / "a.yaml"
    file2 = tmp_settings_dir / "b.yaml"

    with file1.open("w") as f:
        yaml.dump({"app": {"name": "App A", "port": 111}}, f)
    with file2.open("w") as f:
        yaml.dump({"app": {"name": "App B"}}, f)  # B should overwrite A for 'name' if loaded later

    settings = Settings(schema=base_schema, settings_dir=tmp_settings_dir)
    # Glob sorted: a.yaml then b.yaml. So b wins for 'name'.
    assert settings["app"]["name"] == "App B"
    assert settings["app"]["port"] == 111


def test_validation_failure(tmp_settings_dir, base_schema):
    config_file = tmp_settings_dir / "config.yaml"
    # Missing required 'name'
    data = {"app": {"port": "not-an-int"}}
    with config_file.open("w") as f:
        yaml.dump(data, f)

    with pytest.raises(SettingsValidationError):
        Settings(schema=base_schema, settings_dir=tmp_settings_dir)


def test_set_and_save(tmp_settings_dir, base_schema):
    config_file = tmp_settings_dir / "config.yaml"
    with config_file.open("w") as f:
        yaml.dump({"app": {"name": "Original"}}, f)

    settings = Settings(schema=base_schema, settings_dir=tmp_settings_dir)
    settings.set("app.name", "Updated")
    settings.save()

    with config_file.open() as f:
        new_data = yaml.safe_load(f)
    assert new_data["app"]["name"] == "Updated"


def test_remove_key(tmp_settings_dir, base_schema):
    config_file = tmp_settings_dir / "config.yaml"
    with config_file.open("w") as f:
        yaml.dump({"app": {"name": "App"}, "database": {"host": "localhost"}}, f)

    settings = Settings(schema=base_schema, settings_dir=tmp_settings_dir)
    settings.remove("database.host")
    settings.save()

    with config_file.open() as f:
        new_data = yaml.safe_load(f)
    assert "host" not in new_data.get("database", {})


def test_singleton_behavior(tmp_settings_dir, base_schema):
    s1 = Settings(schema=base_schema, settings_dir=tmp_settings_dir)
    s2 = Settings(schema={"other": {"type": "string"}}, settings_dir="/tmp/other")

    assert s1 is s2
    # Second initialization should not have changed settings_dir or schema
    assert s2._settings_dir == tmp_settings_dir
    assert s2._schema == base_schema


def test_get_schema(base_schema):
    settings = Settings(schema=base_schema)
    assert settings.get_schema() == base_schema
    assert settings.get_schema("app") == base_schema["app"]
    assert settings.get_schema("app.name") == base_schema["app"]["schema"]["name"]
    assert settings.get_schema("nonexistent") == {}
