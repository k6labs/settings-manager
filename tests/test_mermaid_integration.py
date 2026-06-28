import pytest
from pathlib import Path
import frontmatter
from settings_manager import Settings, MermaidDiagram

def test_mermaid_extraction_from_markdown(tmp_settings_dir):
    schema = {
        "app": {
            "type": "dict",
            "schema": {
                "name": {"type": "string"},
            }
        },
        "mermaid": {"type": "dict", "schema": {
            "diagram": {"type": "mermaid_diagram"}
        }}
    }
    
    config_file = tmp_settings_dir / "config.md"
    metadata = {"app": {"name": "Test App"}}
    content = """
# App Configuration

```mermaid
stateDiagram-v2
    [*] --> Initializing
    Initializing --> Ready : "Done"
    Ready --> [*]
```
"""
    post = frontmatter.Post(content, **metadata)
    with config_file.open("w", encoding="utf-8") as f:
        f.write(frontmatter.dumps(post))

    settings = Settings(schema=schema, settings_dir=tmp_settings_dir)
    
    # Check if mermaid data was merged
    assert "mermaid" in settings.data
    assert "diagram" in settings["mermaid"]
    diagram = settings["mermaid"]["diagram"]
    assert isinstance(diagram, MermaidDiagram)
    
    # Check states
    assert "Initializing" in diagram.states
    assert "Ready" in diagram.states
    
    # Check transitions
    assert "done" in diagram.transitions
    transition = diagram.transitions["done"]
    assert transition.source == "Initializing"
    assert transition.target == "Ready"

def test_unsupported_mermaid_feature_logs_warning(tmp_settings_dir, caplog):
    schema = {
        "app": {"type": "dict", "allow_unknown": True},
        "mermaid": {"type": "dict", "allow_unknown": True}
    }
    
    config_file = tmp_settings_dir / "unsupported.md"
    content = """
```mermaid
stateDiagram-v2
    state Parent {
        [*] --> Child
    }
```
"""
    with config_file.open("w", encoding="utf-8") as f:
        f.write(content)

    # Should not raise exception during load, but log a warning
    Settings(schema=schema, settings_dir=tmp_settings_dir)
    
    assert "Unsupported Mermaid feature detected: composite_state" in caplog.text

def test_multiple_mermaid_diagrams(tmp_settings_dir):
    schema = {
        "app": {"type": "dict", "allow_unknown": True},
        "mermaid": {"type": "dict", "allow_unknown": True}
    }
    
    config_file = tmp_settings_dir / "multi.md"
    content = """
```mermaid
stateDiagram-v2
    [*] --> S1
```

```mermaid
stateDiagram-v2
    [*] --> S2
```
"""
    with config_file.open("w", encoding="utf-8") as f:
        f.write(content)

    settings = Settings(schema=schema, settings_dir=tmp_settings_dir)
    
    assert "mermaid" in settings.data
    assert "diagram_0" in settings["mermaid"]
    assert "diagram_1" in settings["mermaid"]
