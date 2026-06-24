from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Switch


class SchemaForm(VerticalScroll):
    """
    A widget that generates a form based on a Cerberus schema.
    """

    DEFAULT_CSS = """
    SchemaForm .field-label {
        margin-top: 1;
        text-style: bold;
    }
    SchemaForm .nested-container {
        border-left: solid $primary;
        margin-left: 2;
        padding-left: 2;
        height: auto;
    }
    """

    def __init__(self, schema: dict[str, Any], data: dict[str, Any] | None = None, **kwargs):
        super().__init__(**kwargs)
        self.schema_dict = schema
        self.initial_data = data or {}
        self.inputs: dict[str, Any] = {}

    def compose(self) -> ComposeResult:
        yield from self._generate_fields(self.schema_dict, self.initial_data)

    def _generate_fields(
        self, schema: dict[str, Any], data: dict[str, Any], prefix: str = ""
    ) -> ComposeResult:
        for key, field_schema in schema.items():
            full_key = f"{prefix}{key}"
            field_type = field_schema.get("type", "string")
            value = data.get(key)

            if value is None and "default" in field_schema:
                value = field_schema["default"]

            label_text = field_schema.get("meta", {}).get("label", key.replace("_", " ").title())
            if field_schema.get("required"):
                label_text += " *"

            yield Label(label_text, classes="field-label")

            if field_type == "dict" and "schema" in field_schema:
                with Vertical(classes="nested-container"):
                    yield from self._generate_fields(
                        field_schema["schema"], value or {}, f"{full_key}."
                    )
            elif field_type == "boolean":
                sw = Switch(value=bool(value), id=full_key.replace(".", "__"))
                self.inputs[full_key] = sw
                yield sw
            else:
                # Integer, string, float, etc.
                placeholder = str(field_type)
                if "allowed" in field_schema:
                    placeholder += f" (allowed: {field_schema['allowed']})"

                inp = Input(
                    value=str(value) if value is not None else "",
                    placeholder=placeholder,
                    id=full_key.replace(".", "__"),
                )
                self.inputs[full_key] = inp
                yield inp

    def get_data(self) -> dict[str, Any]:
        """
        Extract data from the form widgets and reconstruct the dictionary.
        """
        result: dict[str, Any] = {}
        for full_key, widget in self.inputs.items():
            if isinstance(widget, Input):
                val: Any = widget.value
                field_schema = self._get_field_schema(full_key)
                field_type = field_schema.get("type", "string")
                if not val and not field_schema.get("required"):
                    val = None
                elif field_type == "integer":
                    try:
                        val = int(val)
                    except ValueError:
                        pass
                elif field_type in ("float", "number"):
                    try:
                        val = float(val)
                    except ValueError:
                        pass
            elif isinstance(widget, Switch):
                val = widget.value
            else:
                continue

            # Insert into nested dictionary
            parts = full_key.split(".")
            target = result
            for part in parts[:-1]:
                if part not in target:
                    target[part] = {}
                target = target[part]
            target[parts[-1]] = val
        return result

    def _get_field_schema(self, full_key: str) -> dict[str, Any]:
        parts = full_key.split(".")
        current_schema = self.schema_dict
        for part in parts[:-1]:
            current_schema = current_schema.get(part, {}).get("schema", {})
        return current_schema.get(parts[-1], {})


class SettingsEditScreen(ModalScreen[dict[str, Any]]):
    """
    A modal screen for editing settings using a generated form.
    """

    DEFAULT_CSS = """
    SettingsEditScreen {
        align: center middle;
    }
    SettingsEditScreen #dialog {
        width: 80%;
        height: 80%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    SettingsEditScreen #screen-title {
        text-align: center;
        width: 100%;
        background: $primary;
        color: $text;
        margin-bottom: 1;
        text-style: bold;
    }
    SettingsEditScreen #buttons {
        height: 3;
        margin-top: 1;
        align: center middle;
    }
    SettingsEditScreen #buttons Button {
        margin: 0 2;
    }
    SettingsEditScreen #form {
        height: 1fr;
    }
    """

    def __init__(
        self,
        schema: dict[str, Any],
        data: dict[str, Any] | None = None,
        title: str = "Edit Settings",
    ):
        super().__init__()
        self.schema_dict = schema
        self.data = data
        self.form_title = title

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label(self.form_title, id="screen-title")
            yield SchemaForm(self.schema_dict, self.data, id="form")
            with Horizontal(id="buttons"):
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", variant="error", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            form = self.query_one(SchemaForm)
            self.dismiss(form.get_data())
        elif event.button.id == "cancel":
            self.dismiss(None)


class TUIApp(App):
    """
    A minimal Textual application to host the SettingsEditScreen.
    """

    def __init__(
        self, schema: dict[str, Any], data: dict[str, Any] | None = None, title: str = "Settings"
    ):
        super().__init__()
        self.schema_dict = schema
        self.data = data
        self.form_title = title
        self.result: dict[str, Any] | None = None

    def on_mount(self) -> None:
        self.push_screen(
            SettingsEditScreen(self.schema_dict, self.data, self.form_title), self.set_result
        )

    def set_result(self, result: dict[str, Any] | None) -> None:
        self.result = result
        self.exit()
