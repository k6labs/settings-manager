# Settings Manager

Settings Manager is a powerful, flexible, and developer-friendly Python library designed to handle application configuration across multiple formats. It simplifies settings management by providing built-in validation, deep merging of directory-based configurations, and a modern Terminal User Interface (TUI) for interactive editing.

Whether you're building a small script or a large-scale application, Settings Manager ensures your configuration is consistent, validated, and easy to maintain.

## 🌟 Key Features

- **🚀 Multi-format Support**: Effortlessly load and save settings from `.yaml`, `.yml`, `.toml`, and `.md` (Markdown with YAML frontmatter).
- **🔄 Deep Merging**: Automatically consolidate multiple configuration files from a directory, with intelligent conflict resolution based on file names.
- **🛡️ Robust Validation**: Powered by [Cerberus](https://docs.python-cerberus.org/), ensuring your settings always adhere to your defined schema.
- **🎨 Interactive TUI**: A beautiful, Textual-based Terminal User Interface for visual settings management without leaving the console.
- **📍 Source Tracking**: Remembers exactly which file each setting came from, allowing you to save changes back to their original sources.
- **🌍 Localization**: Full support for all 24 official EU languages for error messages and CLI help.
- **🧩 Singleton Pattern**: Guaranteed global access to your settings from anywhere in your application.
- **📝 Markdown Integration**: Documentation and configuration living together in harmony using Markdown files with frontmatter.

## 🛠️ Installation

Install Settings Manager using pip:

```bash
pip install settings-manager
```

Or from source:

```bash
git clone https://github.com/richardblaha/settings-manager.git
cd settings-manager
pip install .
```

## 🚀 Quick Start

### 1. Define Your Schema
Settings Manager uses Cerberus for validation. Define your structure and constraints:

```python
# schema.py
SCHEMA = {
    'server': {
        'type': 'dict',
        'schema': {
            'host': {'type': 'string', 'default': 'localhost'},
            'port': {'type': 'integer', 'min': 1024, 'max': 65535, 'required': True},
            'debug': {'type': 'boolean', 'default': False}
        }
    },
    'database': {
        'type': 'dict',
        'schema': {
            'url': {'type': 'string', 'required': True},
            'pool_size': {'type': 'integer', 'default': 10}
        }
    }
}
```

### 2. Basic Usage in Python
Initialize the `Settings` singleton and start using your configuration.

```python
from settings_manager import Settings
from schema import SCHEMA

# Initialize (it loads all files from .settings/ directory by default)
settings = Settings(schema=SCHEMA, settings_dir=".settings")

# Access values using dictionary-like syntax or dot-notation via get()
port = settings['server']['port']
db_url = settings.get('database.url')

# Modify values
settings.set('server.debug', True)

# Validate and save changes back to original files
if settings.validate():
    settings.save()
```

## 🖥️ Command Line Interface

Settings Manager comes with a powerful standalone CLI tool and an easy way to integrate it into your own applications.

### Standalone Usage
```bash
# Get a specific setting
settings-manager get server.port

# Set a value from CLI
settings-manager set server.port 9000

# Open the interactive TUI editor
settings-manager set --tui

# Validate settings files against a schema
settings-manager --schema schema.yaml validate
```

### Integrating into Your App
You can attach Settings Manager commands to your own `argparse` subparsers:

```python
import argparse
from settings_manager import Settings, add_settings_commands

settings = Settings(schema=SCHEMA)
parser = argparse.ArgumentParser(prog='myapp')
subparsers = parser.add_subparsers(dest='command')

# Add 'config' subcommand to your app
config_parser = subparsers.add_parser('config', help='Configure myapp')
add_settings_commands(config_parser.add_subparsers(dest='action'), settings)

args = parser.parse_args()
if hasattr(args, 'func'):
    args.func(args)
```

## 📁 File Organization & Deep Merging

Settings Manager is designed to look into a directory (defaulting to `.settings/`) and merge all supported files:

```text
.settings/
├── 00-defaults.yaml
├── 10-database.toml
└── 20-production.md
```

- **Priority**: Files are loaded in alphabetical order. Later files overwrite values from earlier ones (Deep Merge).
- **Source Preservation**: When you call `save()`, Settings Manager knows which file originally provided each key and updates only that specific file.
- **Markdown Support**: Great for providing context. Settings are stored in the YAML frontmatter, and the Markdown body is kept intact during saves.

## 🌈 Interactive TUI

The built-in TUI (Terminal User Interface) makes it easy for users to configure your application without manual file editing.

- **Automated Form Generation**: Forms are automatically created based on your Cerberus schema.
- **Real-time Validation**: Input is validated against the schema as you type or submit.
- **Nested Structures**: Support for complex, nested configuration dictionaries.

To launch the TUI, use the `--tui` flag with the `set` command:
```bash
settings-manager set --tui
```

## 🌍 Localization

The library is fully localized. You can specify the language during initialization:

```python
settings = Settings(schema=SCHEMA, language="cs")  # Czech
```

Supported languages include all 24 official EU languages:
`bg`, `cs`, `da`, `de`, `el`, `en`, `es`, `et`, `fi`, `fr`, `ga`, `hr`, `hu`, `it`, `lt`, `lv`, `mt`, `nl`, `pl`, `pt`, `ro`, `sk`, `sl`, `sv`.

## 🧪 Development

Setting up the development environment:

```bash
# Install with dev and test dependencies
pip install -e ".[dev,test]"

# Run test suite
pytest

# Quality checks
ruff check .
mypy src
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
