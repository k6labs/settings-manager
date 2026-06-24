import gettext
import logging
import threading
import tomllib
from pathlib import Path
from typing import Any, Optional

import frontmatter
import tomli_w
import yaml
from cerberus import Validator

logger = logging.getLogger(__name__)


class SettingsValidationError(Exception):
    """Custom exception raised for configuration validation failures."""

    pass


class Settings:
    """
    Singleton class to manage application settings from YAML and Markdown files.

    It supports loading, merging, validating, and saving settings while tracking
    the source file for each configuration key.
    """

    _instance: Optional["Settings"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    @classmethod
    def reset(cls):
        """
        Reset the singleton instance.
        Mainly used for testing purposes to ensure a clean state.
        """
        with cls._lock:
            cls._instance = None

    def __init__(
        self,
        schema: dict[str, Any],
        settings_dir: str | Path = ".settings",
        language: str = "en",
    ):
        """
        Initialize the Settings instance.

        Args:
            schema: Cerberus validation schema.
            settings_dir: Directory to load settings from.
            language: Language code for error messages ('en' or 'cs').
        """
        if self._initialized:
            return

        self._language = language
        self._locale_dir = Path(__file__).parent / "locale"
        self._translation = gettext.translation(
            "settings", localedir=str(self._locale_dir), languages=[self._language], fallback=True
        )

        self._settings_dir = Path(settings_dir)
        self._data: dict[str, Any] = {}
        self._source_mapping: dict[tuple[str, ...], Path] = {}
        self._md_bodies: dict[Path, str] = {}
        self._loaded_files: set[Path] = set()
        self._schema = schema

        self.load()
        self._initialized = True

    def _t(self, msg_id: str, **kwargs) -> str:
        """
        Translate a message key based on the initialized language.

        Args:
            msg_id: Translation key.
            **kwargs: Formatting arguments for the translation string.

        Returns:
            Formatted translation string.
        """
        template = self._translation.gettext(msg_id)
        return template.format(**kwargs)

    @property
    def data(self) -> dict[str, Any]:
        """
        Get the consolidated settings data.

        Returns:
            Dictionary containing all loaded and validated settings.
        """
        return self._data

    def __getitem__(self, key: str) -> Any:
        """
        Access settings data using dictionary key syntax.

        Args:
            key: Setting key to retrieve.

        Returns:
            The value associated with the key.
        """
        return self._data[key]

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a setting value with a default fallback.
        Supports dot notation (e.g., 'app.port').

        Args:
            key: Setting key.
            default: Value to return if the key is not found.

        Returns:
            Setting value or default.
        """
        if not key:
            return self._data

        parts = key.split(".")
        val = self._data
        try:
            for part in parts:
                val = val[part]
            return val
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """
        Set a setting value using dot notation.

        Args:
            key: Setting key (e.g., 'app.port').
            value: Value to set.
        """
        parts = key.split(".")
        d = self._data
        path_tuple = tuple(parts)

        # Navigate to the parent dictionary
        for part in parts[:-1]:
            if part not in d or not isinstance(d[part], dict):
                d[part] = {}
            d = d[part]

        d[parts[-1]] = value

        # If it's a new key without mapping, assign it to the first loaded file or a default
        if path_tuple not in self._source_mapping:
            if self._loaded_files:
                self._source_mapping[path_tuple] = sorted(self._loaded_files)[0]
            else:
                default_file = self._settings_dir / "settings.yaml"
                self._source_mapping[path_tuple] = default_file
                self._loaded_files.add(default_file)

    def remove(self, key: str):
        """
        Remove a setting key using dot notation.

        Args:
            key: Setting key to remove.
        """
        parts = key.split(".")
        d = self._data

        # Navigate to the parent
        for part in parts[:-1]:
            if part not in d or not isinstance(d[part], dict):
                return
            d = d[part]

        if parts[-1] in d:
            del d[parts[-1]]

        # Clean up source mapping
        path_tuple = tuple(parts)
        if path_tuple in self._source_mapping:
            del self._source_mapping[path_tuple]

        # Also remove sub-keys from mapping if any
        keys_to_del = [k for k in self._source_mapping if k[: len(path_tuple)] == path_tuple]
        for k in keys_to_del:
            del self._source_mapping[k]

    def validate(self) -> bool:
        """
        Validate the current settings against the schema.

        Returns:
            True if validation passes.

        Raises:
            SettingsValidationError: If validation fails.
        """
        v = Validator(self._schema)
        if not v.validate(self._data):
            logger.error(self._t("validation_errors"))
            logger.error(yaml.dump(v.errors, default_flow_style=False))
            raise SettingsValidationError(self._t("validation_failed"))
        return True

    def get_schema(self, key: str | None = None) -> dict[str, Any]:
        """
        Retrieve the Cerberus schema for a specific configuration key.

        Args:
            key: Dot notation key. If None, returns the root schema.

        Returns:
            Dictionary containing the schema for the requested key.
        """
        if not key:
            return self._schema

        parts = key.split(".")
        current = self._schema
        for i, part in enumerate(parts):
            if part in current:
                if i == len(parts) - 1:
                    return current[part]
                if "schema" in current[part]:
                    current = current[part]["schema"]
                else:
                    return {}
            else:
                return {}
        return {}

    def edit_tui(self, key: str | None = None, parent_app: Any | None = None):
        """
        Open a Textual TUI to edit settings.

        Args:
            key: Optional dot-notation key to edit a specific sub-section.
            parent_app: Optional running Textual App instance. If provided, the TUI
                        will be pushed as a modal screen onto this app.
        """
        from .tui import SettingsEditScreen, TUIApp

        target_schema = self.get_schema(key)
        target_data = self.get(key)
        is_wrapped = False

        if not isinstance(target_data, dict) and target_data is not None and key:
            # If it's a leaf node, we wrap it to use SchemaForm which expects a dict.
            is_wrapped = True
            last_part = key.split(".")[-1]
            parent_key = ".".join(key.split(".")[:-1])
            target_schema = {last_part: self.get_schema(parent_key).get(last_part, {})}
            target_data = {last_part: target_data}

        title = self._t("cli_help_set") + f": {key or ''}"

        def handle_result(result: dict[str, Any] | None):
            if result is not None:
                if key:
                    # If we wrapped it, unwrap it
                    if is_wrapped:
                        last_part = key.split(".")[-1]
                        new_val = result.get(last_part)
                    else:
                        new_val = result
                    self.set(key, new_val)
                else:
                    for k, v in result.items():
                        self.set(k, v)

                self.validate()
                self.save()

        if parent_app:
            parent_app.push_screen(
                SettingsEditScreen(schema=target_schema, data=target_data, title=title),
                handle_result,
            )
        else:
            app = TUIApp(schema=target_schema, data=target_data, title=title)
            app.run()
            handle_result(app.result)

    def _deep_merge(
        self,
        base: dict[str, Any],
        source: dict[str, Any],
        path: Path,
        current_path: tuple[str, ...] = (),
    ):
        """
        Recursively merge source dictionary into base dictionary.

        Tracks the origin file for each leaf node in the configuration tree.

        Args:
            base: Target dictionary.
            source: Source dictionary to merge.
            path: Path to the source file.
            current_path: Tuple representing the path in the configuration hierarchy.
        """
        for key, value in source.items():
            new_path = (*current_path, key)
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value, path, new_path)
            else:
                base[key] = value
                self._source_mapping[new_path] = path

    def load(self):
        """
        Load all configuration files from the settings directory.

        Files with .md, .yaml, .yml, or .toml extensions are loaded and merged.
        The final result is validated against the provided schema.

        Raises:
            SettingsValidationError: If a file cannot be loaded or validation fails.
        """
        if not self._settings_dir.exists():
            self._settings_dir.mkdir(parents=True, exist_ok=True)
            logger.info(self._t("dir_created", path=self._settings_dir))

        merged_data: dict[str, Any] = {}
        extensions = {".md", ".yaml", ".yml", ".toml"}
        files = sorted([f for f in self._settings_dir.iterdir() if f.suffix.lower() in extensions])

        for file_path in files:
            try:
                suffix = file_path.suffix.lower()
                if suffix == ".md":
                    post = frontmatter.load(file_path)
                    file_data = post.metadata
                    self._md_bodies[file_path] = post.content
                elif suffix == ".toml":
                    with file_path.open("rb") as f:
                        file_data = tomllib.load(f)
                else:
                    with file_path.open(encoding="utf-8") as f:
                        file_data = yaml.safe_load(f) or {}

                self._loaded_files.add(file_path)
                self._deep_merge(merged_data, file_data, file_path)
            except Exception as e:
                msg = self._t("load_error", path=file_path, error=e)
                logger.error(msg)
                raise SettingsValidationError(msg) from e

        v = Validator(self._schema)
        if not v.validate(merged_data):
            logger.error(self._t("validation_errors"))
            logger.error(yaml.dump(v.errors, default_flow_style=False))
            raise SettingsValidationError(self._t("validation_failed"))

        self._data = v.normalized(merged_data)

    def save(self):
        """
        Save the current settings data back to the original files.

        Only keys that were originally present in a file or whose parent
        path was tracked are saved back to their respective files.

        Raises:
            IOError: If saving to a file fails.
        """
        file_contents: dict[Path, dict[str, Any]] = {path: {} for path in self._loaded_files}

        def build_file_data(data: Any, current_path: tuple[str, ...]):
            if isinstance(data, dict):
                for key, value in data.items():
                    new_path = (*current_path, key)
                    if new_path in self._source_mapping:
                        target_file = self._source_mapping[new_path]
                        d = file_contents[target_file]
                        for p_key in current_path:
                            d = d.setdefault(p_key, {})
                        d[key] = value
                    else:
                        build_file_data(value, new_path)

        build_file_data(self._data, ())

        for file_path, data in file_contents.items():
            try:
                suffix = file_path.suffix.lower()
                if suffix == ".md":
                    content = self._md_bodies.get(file_path, "")
                    post = frontmatter.Post(content, **data)
                    with file_path.open("w", encoding="utf-8") as f:
                        f.write(frontmatter.dumps(post))
                elif suffix == ".toml":
                    with file_path.open("wb") as f:
                        tomli_w.dump(data, f)
                else:
                    with file_path.open("w", encoding="utf-8") as f:
                        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            except Exception as e:
                msg = self._t("save_error", path=file_path, error=e)
                logger.error(msg)
                raise OSError(msg) from e
