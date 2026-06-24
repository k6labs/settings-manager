import pytest
from textual.app import App
from textual.widgets import Input, Label, Switch

from settings_manager.tui import SchemaForm


class MockApp(App):
    pass


@pytest.mark.anyio
async def test_schema_form_generation():
    schema = {
        "name": {"type": "string", "default": "John"},
        "age": {"type": "integer"},
        "active": {"type": "boolean", "default": True},
        "metadata": {"type": "dict", "schema": {"version": {"type": "integer", "default": 1}}},
    }
    data = {"age": 30}

    app = MockApp()
    async with app.run_test():
        form = SchemaForm(schema, data)
        # We need to simulate the composition context for Vertical to work
        # Or we can just check if widgets are yielded correctly by mocking Vertical
        from unittest.mock import patch

        with patch("settings_manager.tui.Vertical") as mock_vertical:
            widgets = list(form._generate_fields(schema, data))

            widget_types = [type(w) for w in widgets]
            assert Label in widget_types
            assert Input in widget_types
            assert Switch in widget_types
            # Vertical was called
            assert mock_vertical.called


@pytest.mark.anyio
async def test_schema_form_get_data():
    schema = {"name": {"type": "string"}, "age": {"type": "integer"}, "active": {"type": "boolean"}}
    app = MockApp()
    async with app.run_test():
        form = SchemaForm(schema)

        # Mock inputs
        name_input = Input(value="Alice")
        age_input = Input(value="25")
        active_switch = Switch(value=False)

        form.inputs = {"name": name_input, "age": age_input, "active": active_switch}

        data = form.get_data()
        assert data == {"name": "Alice", "age": 25, "active": False}


@pytest.mark.anyio
async def test_schema_form_nested_get_data():
    schema = {"app": {"type": "dict", "schema": {"port": {"type": "integer"}}}}
    app = MockApp()
    async with app.run_test():
        form = SchemaForm(schema)
        port_input = Input(value="8080")
        form.inputs = {"app.port": port_input}

        data = form.get_data()
        assert data == {"app": {"port": 8080}}


@pytest.mark.anyio
async def test_tui_app_flow():
    from settings_manager.tui import TUIApp

    schema = {"title": {"type": "string"}}
    data = {"title": "Hello"}

    app = TUIApp(schema, data)
    async with app.run_test() as pilot:
        # Check if screen is pushed
        from settings_manager.tui import SettingsEditScreen

        assert isinstance(app.screen, SettingsEditScreen)

        # In Textual, pilot.click targets the center of the widget.
        # Let's use pilot.click("#form Input") or similar to be sure.
        # But since we fixed the ID collision, #title should now refer to the Input.
        await pilot.click("#title")

        # Instead of many backspaces, we can use pilot.press("ctrl+a", "backspace")
        # which is supported by Textual Input widget.
        # However, it seems ctrl+a didn't work as expected in the test environment.
        # Let's use many backspaces or just clear the value directly if possible.
        # Textual's Pilot can also use pilot.press("home", "shift+end", "backspace")
        await pilot.press("home", "shift+end", "backspace")
        await pilot.press(*"World")
        await pilot.press("enter")

        # Click save
        await pilot.click("#save")

        # Verify app result
        assert app.result == {"title": "World"}
