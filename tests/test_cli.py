import argparse
import sys
from unittest.mock import patch

import yaml

from settings_manager import Settings, add_settings_commands
from settings_manager.cli import main


def test_cli_get(tmp_settings_dir, base_schema, capsys):
    config_file = tmp_settings_dir / "config.yaml"
    with config_file.open("w") as f:
        yaml.dump({"app": {"name": "CLI App"}}, f)

    settings = Settings(schema=base_schema, settings_dir=tmp_settings_dir)
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action")
    add_settings_commands(subparsers, settings)

    args = parser.parse_args(["get", "app.name"])
    args.func(args)

    captured = capsys.readouterr()
    assert "CLI App" in captured.out


def test_cli_set(tmp_settings_dir, base_schema, capsys):
    config_file = tmp_settings_dir / "config.yaml"
    with config_file.open("w") as f:
        yaml.dump({"app": {"name": "Original"}}, f)

    settings = Settings(schema=base_schema, settings_dir=tmp_settings_dir)
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action")
    add_settings_commands(subparsers, settings)

    args = parser.parse_args(["set", "app.port", "1234"])
    args.func(args)

    captured = capsys.readouterr()
    assert "app.port" in captured.out

    with config_file.open() as f:
        data = yaml.safe_load(f)
    assert data["app"]["port"] == 1234


def test_cli_validate(tmp_settings_dir, base_schema, capsys):
    config_file = tmp_settings_dir / "config.yaml"
    with config_file.open("w") as f:
        yaml.dump({"app": {"name": "Valid App"}}, f)

    settings = Settings(schema=base_schema, settings_dir=tmp_settings_dir)
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action")
    add_settings_commands(subparsers, settings)

    args = parser.parse_args(["validate"])
    args.func(args)

    captured = capsys.readouterr()
    assert "valid" in captured.out.lower()


def test_cli_remove(tmp_settings_dir, base_schema, capsys):
    config_file = tmp_settings_dir / "config.yaml"
    # Use valid fields from schema
    with config_file.open("w") as f:
        yaml.dump({"app": {"name": "App"}, "database": {"host": "localhost"}}, f)

    settings = Settings(schema=base_schema, settings_dir=tmp_settings_dir)
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action")
    add_settings_commands(subparsers, settings)

    args = parser.parse_args(["remove", "database.host"])
    args.func(args)

    captured = capsys.readouterr()
    assert "removed" in captured.out.lower()

    with config_file.open() as f:
        data = yaml.safe_load(f)
    assert "host" not in data.get("database", {})


def test_cli_main_entrypoint(tmp_settings_dir, base_schema, capsys):
    # Create schema file (outside settings_dir to avoid it being loaded as data)
    schema_file = tmp_settings_dir.parent / "schema.yaml"
    with schema_file.open("w") as f:
        yaml.dump(base_schema, f)

    # Create settings file
    config_file = tmp_settings_dir / "config.yaml"
    with config_file.open("w") as f:
        yaml.dump({"app": {"name": "Main App"}}, f)

    # Mock sys.argv to simulate: settings-manager --schema schema.yaml --dir .settings get app.name
    test_args = [
        "settings-manager",
        "--schema",
        str(schema_file),
        "--dir",
        str(tmp_settings_dir),
        "get",
        "app.name",
    ]

    with patch.object(sys, "argv", test_args):
        main()

    captured = capsys.readouterr()
    assert "Main App" in captured.out
