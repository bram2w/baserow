from prosemirror.model import Schema
from prosemirror.schema.basic import br_dom, p_dom

# Look at
# https://github.com/fellowapp/prosemirror-py/blob/main/prosemirror/schema/basic/schema_basic.py
# for the original source code of the basic schema.

nodes = {
    "doc": {"content": "block+"},
    "paragraph": {
        "content": "inline*",
        "group": "block",
        "parseDOM": [{"tag": "p"}],
        "toDOM": lambda _: p_dom,
    },
    "text": {"group": "inline"},
    "hardBreak": {
        "inline": True,
        "group": "inline",
        "selectable": False,
        "parseDOM": [{"tag": "br"}],
        "toDOM": lambda _: br_dom,
    },
    "mention": {
        "group": "inline",
        "inline": True,
        "attrs": {"id": {"default": None}, "label": {"default": None}},
        "toDOM": lambda node: [
            "span",
            {
                "class": "mention",
                "data-id": node.attrs["id"],
                "data-label": node.attrs["label"],
                "data-type": "mention",
                "contenteditable": "false",
            },
            "@" + node.attrs["name"],
        ],
        "parseDOM": [
            {
                "tag": "span[data-id]",
                "getAttrs": lambda dom: {
                    "id": dom.getAttribute("data-id"),
                    "label": dom.getAttribute("data-label"),
                },
            }
        ],
    },
}


schema = Schema({"nodes": nodes, "marks": {}})
