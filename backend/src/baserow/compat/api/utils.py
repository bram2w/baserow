def prefix_schema_description_deprecated(
    see_other_heading: str = None,
    see_other_url: str = None,
    deprecation_in_year: int = None,
) -> str:
    """
    A helper function which generates a prefix we'll add
    to deprecated endpoint DRF spectacular descriptions.
    """

    message = "**This endpoint has been deprecated"
    if any({see_other_heading, see_other_url}):
        message += (
            " and replaced with a new endpoint, "
            f"[{see_other_heading}]({see_other_url})"
        )
    if deprecation_in_year:
        message += (
            f".**\n\n**Support for this endpoint will end in {deprecation_in_year}"
        )
    message += ".**\n\n"
    return message
