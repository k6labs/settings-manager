import frontmatter

from settings_manager import Settings


def test_loading_markdown(tmp_settings_dir, base_schema):
    config_file = tmp_settings_dir / "config.md"
    metadata = {"app": {"name": "Markdown App", "port": 8888}}
    content = "This is the markdown body text."

    post = frontmatter.Post(content, **metadata)
    with config_file.open("w", encoding="utf-8") as f:
        f.write(frontmatter.dumps(post))

    settings = Settings(schema=base_schema, settings_dir=tmp_settings_dir)
    assert settings["app"]["name"] == "Markdown App"
    assert settings["app"]["port"] == 8888

    # Check if body is preserved internally
    assert settings._md_bodies[config_file] == content


def test_save_markdown_preserves_body(tmp_settings_dir, base_schema):
    config_file = tmp_settings_dir / "config.md"
    metadata = {"app": {"name": "Markdown App"}}
    content = "Original markdown body."

    post = frontmatter.Post(content, **metadata)
    with config_file.open("w", encoding="utf-8") as f:
        f.write(frontmatter.dumps(post))

    settings = Settings(schema=base_schema, settings_dir=tmp_settings_dir)
    settings.set("app.name", "Updated Markdown App")
    settings.save()

    # Read back and verify
    post_new = frontmatter.load(config_file)
    assert post_new.metadata["app"]["name"] == "Updated Markdown App"
    assert post_new.content == content
