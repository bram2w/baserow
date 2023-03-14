from baserow.compat.api.utils import prefix_schema_description_deprecated


def test_prefix_schema_description_deprecated(group_compat_timebomb):

    # With no link or year
    without_link_or_year = prefix_schema_description_deprecated()
    assert without_link_or_year == "**This endpoint has been deprecated.**\n\n"

    # With no link, with year
    without_link_or_year = prefix_schema_description_deprecated(
        deprecation_in_year=2023
    )
    assert (
        without_link_or_year == "**This endpoint has been "
        "deprecated.**\n\n**Support for this endpoint "
        "will end in 2023.**\n\n"
    )

    # With link, without year
    without_link_or_year = prefix_schema_description_deprecated(
        "list_workspaces", "#tag/Workspaces/operation/list_workspaces"
    )
    assert (
        without_link_or_year == "**This endpoint has been deprecated and replaced with "
        "a new endpoint, [list_workspaces](#tag/Workspaces/operation/list_workspaces)."
        "**\n\n"
    )

    # With link, with year
    without_link_or_year = prefix_schema_description_deprecated(
        "list_workspaces", "#tag/Workspaces/operation/list_workspaces", 2023
    )
    assert (
        without_link_or_year == "**This endpoint has been deprecated and replaced with "
        "a new endpoint, [list_workspaces](#tag/Workspaces/operation/list_workspaces)."
        "**\n\n**Support for this endpoint will end in 2023.**\n\n"
    )
