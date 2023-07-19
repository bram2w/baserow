from baserow.core.prosemirror.utils import (
    extract_mentioned_user_ids,
    is_valid_prosemirror_document,
)


def test_valid_prosemirror_doc_can_be_parsed():
    random_doc = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "hey "},
                    {"type": "mention", "attrs": {"id": 1, "label": "staff-dev"}},
                    {
                        "type": "text",
                        "text": " Lorem Ipsum is simply dummy text of the printing and typesetting industry.",
                    },
                    {"type": "hardBreak"},
                    {"type": "hardBreak"},
                    {"type": "hardBreak"},
                    {"type": "text", "text": "Lorem"},
                ],
            }
        ],
    }

    assert is_valid_prosemirror_document(random_doc) is True

    mentioned_user_ids = extract_mentioned_user_ids(random_doc)
    assert mentioned_user_ids == {1}
