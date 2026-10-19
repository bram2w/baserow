import pytest

from baserow_enterprise.assistant.tools.mcp_meta import get_mcp_meta, mcp_tool


def test_mcp_tool_sets_meta_and_keeps_function():
    @mcp_tool(title="List pages", group="builder_read", read_only=True)
    def list_pages(ctx, builder_id: int, thought: str):
        return builder_id

    meta = get_mcp_meta(list_pages)
    assert meta.title == "List pages"
    assert meta.group == "builder_read"
    assert meta.read_only and not meta.destructive
    assert list_pages(None, 3, "") == 3


def test_undecorated_function_has_no_meta():
    def navigate(ctx): ...

    assert get_mcp_meta(navigate) is None


def test_read_only_and_destructive_are_exclusive():
    with pytest.raises(ValueError):
        mcp_tool(title="x", group="g", read_only=True, destructive=True)
