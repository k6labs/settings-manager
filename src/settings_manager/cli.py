import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

from .settings import Settings, SettingsValidationError

logger = logging.getLogger(__name__)


class SettingsCLI:
    """
    Command Line Interface handler for Settings management.

    Provides methods to interact with a Settings instance via CLI commands,
    including retrieval, modification, removal, and validation of settings.
    """

    def __init__(self, settings: Settings):
        """
        Initialize the CLI handler with a Settings instance.

        Args:
            settings: The Settings instance to manage.
        """
        self.settings = settings

    def get(self, key: str | None = None) -> None:
        """
        Retrieve and print the value of a setting key.

        If no key is provided, the entire settings dictionary is printed.
        Supports dot notation for nested keys.

        Args:
            key: The configuration key to retrieve (e.g., 'app.port').
        """
        value = self.settings.get(key)

        if value is None and key is not None:
            print(self.settings._t("cli_key_not_found", key=key), file=sys.stderr)
            return

        if isinstance(value, (dict, list)):
            print(json.dumps(value, indent=2, ensure_ascii=False))
        else:
            print(value)

    def set(self, key: str | None = None, value_str: str | None = None, tui: bool = False) -> None:
        """
        Set a configuration key to a value, validate, and save.

        The value string is attempted to be parsed as JSON to support
        types such as integers, booleans, and lists.

        Args:
            key: The configuration key to set.
            value_str: The value to set, as a string.
            tui: Whether to use a Textual TUI for editing.
        """
        if tui:
            try:
                self.settings.edit_tui(key)
                return
            except Exception as e:
                logger.error(self.settings._t("cli_save_error", error=str(e)))
                print(self.settings._t("cli_save_error", error=str(e)), file=sys.stderr)
                sys.exit(1)

        if key is None:
            print("Error: key is required when not using --tui", file=sys.stderr)
            sys.exit(1)

        if value_str is None:
            print("Error: value is required when not using --tui", file=sys.stderr)
            sys.exit(1)

        try:
            value = json.loads(value_str)
        except json.JSONDecodeError:
            value = value_str

        try:
            self.settings.set(key, value)
            self.settings.validate()
            self.settings.save()
            print(self.settings._t("cli_set_success", key=key, value=value))
        except SettingsValidationError as e:
            print(self.settings._t("cli_config_invalid", error=str(e)), file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            logger.error(self.settings._t("cli_save_error", error=str(e)))
            print(self.settings._t("cli_save_error", error=str(e)), file=sys.stderr)
            sys.exit(1)

    def remove(self, key: str) -> None:
        """
        Remove a configuration key and save the changes.

        Args:
            key: The configuration key to remove.
        """
        try:
            self.settings.remove(key)
            self.settings.save()
            print(self.settings._t("cli_remove_success", key=key))
        except Exception as e:
            logger.error(self.settings._t("cli_remove_error", error=str(e)))
            print(self.settings._t("cli_remove_error", error=str(e)), file=sys.stderr)
            sys.exit(1)

    def validate(self) -> None:
        """
        Validate the current settings against the defined schema.
        """
        try:
            self.settings.validate()
            print(self.settings._t("cli_config_valid"))
        except SettingsValidationError as e:
            print(self.settings._t("cli_config_invalid", error=str(e)), file=sys.stderr)
            sys.exit(1)


def add_settings_commands(subparsers: Any, settings: Settings) -> None:
    """
    Register settings subcommands to an argparse subparser.

    Adds 'get', 'set', 'remove', and 'validate' commands to the provided subparser.

    Args:
        subparsers: The argparse subparsers object to add commands to.
        settings: The Settings instance to be used by the CLI handler.
    """
    cli = SettingsCLI(settings)

    # Get command
    get_parser = subparsers.add_parser(
        "get",
        help=settings._t("cli_help_get") if hasattr(settings, "_t") else "Get a setting value",
    )
    get_parser.add_argument("key", nargs="?", help="Key to get (dot notation)")
    get_parser.set_defaults(func=lambda args: cli.get(args.key))

    # Set command
    set_parser = subparsers.add_parser(
        "set",
        help=settings._t("cli_help_set") if hasattr(settings, "_t") else "Set a setting value",
    )
    set_parser.add_argument("key", nargs="?", help="Key to set (dot notation)")
    set_parser.add_argument(
        "value", nargs="?", help="Value to set (JSON formatted for non-strings)"
    )
    set_parser.add_argument("--tui", action="store_true", help="Use TUI for editing")
    set_parser.set_defaults(func=lambda args: cli.set(args.key, args.value, args.tui))

    # Remove command
    remove_parser = subparsers.add_parser(
        "remove",
        help=settings._t("cli_help_remove") if hasattr(settings, "_t") else "Remove a setting key",
    )
    remove_parser.add_argument("key", help="Key to remove (dot notation)")
    remove_parser.set_defaults(func=lambda args: cli.remove(args.key))

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help=settings._t("cli_help_validate") if hasattr(settings, "_t") else "Validate settings",
    )
    validate_parser.set_defaults(func=lambda args: cli.validate())


def main() -> None:
    """
    Main entry point for the settings-manager CLI.
    """
    parser = argparse.ArgumentParser(
        prog="settings-manager", description="Manage application settings"
    )
    parser.add_argument("--schema", type=str, help="Path to Cerberus schema (YAML)")
    parser.add_argument("--dir", type=str, default=".settings", help="Settings directory")
    parser.add_argument("--lang", default="en", help="Language for messages")

    # Parse known args first to get settings initialization params
    args, remaining = parser.parse_known_args()

    schema = {}
    if args.schema:
        schema_path = Path(args.schema)
        try:
            with schema_path.open(encoding="utf-8") as f:
                schema = yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading schema: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        settings = Settings(schema=schema, settings_dir=args.dir, language=args.lang)
    except Exception as e:
        print(f"Error initializing settings: {e}", file=sys.stderr)
        sys.exit(1)

    subparsers = parser.add_subparsers(dest="command", required=True)
    add_settings_commands(subparsers, settings)

    # Parse everything
    args = parser.parse_args(remaining, namespace=args)

    if hasattr(args, "func"):
        args.func(args)


if __name__ == "__main__":
    main()
