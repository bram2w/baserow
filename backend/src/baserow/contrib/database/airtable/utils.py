import re


def extract_share_id_from_url(public_base_url: str) -> str:
    """
    Extracts the Airtable share id from the provided URL.

    :param public_base_url: The URL where the share id must be extracted from.
    :raises ValueError: If the provided URL doesn't match the publicly shared
        Airtable URL.
    :return: The extracted share id.
    """

    result = re.search(r"https:\/\/airtable.com\/(shr|app)(.*)$", public_base_url)

    if not result:
        raise ValueError(
            f"Please provide a valid shared Airtable URL (e.g. "
            f"https://airtable.com/shrxxxxxxxxxxxxxx)"
        )

    return f"{result.group(1)}{result.group(2)}"


def get_airtable_row_primary_value(table, row):
    """
    Tries to extract the name of a row using the primary value. If empty or not
    available, then it falls back on the row ID>

    :param table: The table where to extract primary column ID from.
    :param row: The row to get the value name for.
    :return: The primary value or ID of the row.
    """

    primary_column_id = table.get("primaryColumnId", "")
    primary_value = row.get("cellValuesByColumnId", {}).get(primary_column_id, None)

    if not primary_value or not isinstance(primary_value, str):
        primary_value = row["id"]

    return primary_value


def quill_parse_inline(insert, attributes):
    if "bold" in attributes:
        insert = f"**{insert}**"
    if "italic" in attributes:
        insert = f"_{insert}_"
    if "strike" in attributes:
        insert = f"~{insert}~"
    if "code" in attributes:
        insert = f"`{insert}`"
    if "link" in attributes:
        insert = f"[{insert}]({attributes['link']})"
    if isinstance(insert, object) and "mention" in insert:
        insert = f"@{insert['mention'].get('userId', '')}"

    return insert


def quill_wrap_block(attributes):
    prepend = ""
    append = ""
    multi_line = False
    if "header" in attributes:
        prepend = "#" * attributes["header"] + " "
    if "list" in attributes:
        list_type = attributes["list"]
        prepend = " " * attributes.get("indent", 0) * 4
        if list_type == "ordered":
            prepend += f"1. "
        elif list_type == "bullet":
            prepend += "- "
        elif list_type == "unchecked":
            prepend += "- [ ] "
        elif list_type == "checked":
            prepend += "- [x] "
    if "blockquote" in attributes:
        prepend = "> "
    if "≈≈" in attributes:
        prepend = "> "
    if "code-block" in attributes:
        prepend = "```\n"
        append = "```\n"
        multi_line = True
    return prepend, append, multi_line


def quill_split_with_newlines(value):
    parts = re.split(r"(\n)", value)
    if parts and parts[0] == "":
        parts.pop(0)
    if parts and parts[-1] == "":
        parts.pop()
    return parts


def quill_to_markdown(ops: list) -> str:
    """
    Airtable uses the QuillJS editor for their rich text field. There is no library
    to convert it in Baserow compatible markdown. This is a simple, custom written
    function to convert it to Baserow compatible markdown.

    The format is a bit odd because a newline entry can define how it should have been
    formatted as on block level, making it a bit tricky because it's not sequential.

    See the `test_quill_to_markdown_airtable_example` test for an example.

    :param ops: The QuillJS delta object that must be converted to markdown.
    :return: The converted markdown string.
    """

    md_output = []
    # Holds everything that must be written as a line. Each entry in the ops can add to
    # it until a "\n" character is detected.
    current_object = ""
    # Temporarily holds markdown code that has start and ending block, like with
    # code "```", for example. Need to temporarily store the prepend and append values,
    # so that we can add to it if it consists of multiple lines.
    current_multi_line = None

    def flush_line():
        nonlocal md_output
        nonlocal current_object
        if current_object != "":
            md_output.append(current_object)
            current_object = ""

    def flush_multi_line(current_prepend, current_append):
        nonlocal current_object
        nonlocal current_multi_line
        if current_multi_line is not None and current_multi_line != (
            current_prepend,
            current_append,
        ):
            current_object = (
                current_multi_line[0] + current_object + current_multi_line[1]
            )
            flush_line()
            current_multi_line = None

    for index, op in enumerate(ops):
        raw_insert = op.get("insert", "")
        attributes = op.get("attributes", {})

        if isinstance(raw_insert, str):
            insert_lines = quill_split_with_newlines(raw_insert)
        else:
            insert_lines = [raw_insert]

        # Break the insert by "\n" because the block formatting options should only
        # refer to the previous line.
        for insert_line in insert_lines:
            is_new_line = insert_line == "\n"

            if is_new_line:
                prepend, append, multi_line = quill_wrap_block(attributes)
                flush_multi_line(prepend, append)

                # Starting a new multi-line block. All the following lines will be
                # enclosed by the prepend and append.
                if multi_line and current_multi_line is None:
                    current_multi_line = (prepend, append)

            parsed_insert = quill_parse_inline(insert_line, attributes)
            current_object += parsed_insert

            if is_new_line and not multi_line:
                current_object = prepend + current_object + append
                flush_line()

    flush_multi_line(None, None)
    flush_line()

    return "".join(md_output).strip()
