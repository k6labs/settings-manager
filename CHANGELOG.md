# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-24

### Added
- **Core**: Initial release of Settings Manager.
- **Formats**: Support for YAML, TOML, and Markdown (with YAML frontmatter).
- **Architecture**: Singleton pattern for centralized settings access.
- **Merging**: Deep merge functionality for multiple configuration files.
- **Validation**: Schema-based validation using Cerberus.
- **Persistence**: Source tracking for atomic saves back to original files.
- **I18n**: Localization support for all 24 official EU languages using gettext.
- **UI**: Interactive TUI editor based on the Textual framework.
- **CLI**: Robust standalone `settings-manager` tool and integration API for custom apps.
- **DevOps**: GitHub Actions for CI, Ruff for linting/formatting, and Mypy for type checking.

### Changed
- Improved CLI argument parsing to handle global options more intuitively.
- Consistent use of `pathlib` for all file and directory operations.

### Fixed
- Corrected field definition retrieval in `get_schema` for nested leaf nodes.
- Resolved CLI parsing issues when mixing global flags with subcommands.
