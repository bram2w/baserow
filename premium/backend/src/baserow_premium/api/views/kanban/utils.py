from baserow_premium.api.views.exceptions import InvalidSelectOptionParameter


def prepare_kanban_view_parameters(request):
    # Parse the provided select options from the query parameters. It's possible
    # to only fetch the rows of specific field options and also filter on them.
    all_select_options = request.GET.getlist("select_option")
    included_select_options = {}
    for select_option in all_select_options:
        splitted = select_option.split(",")
        try:
            included_select_options[splitted[0]] = {}
            if 1 < len(splitted):
                included_select_options[splitted[0]]["limit"] = int(splitted[1])
            if 2 < len(splitted):
                included_select_options[splitted[0]]["offset"] = int(splitted[2])
        except ValueError:
            raise InvalidSelectOptionParameter(splitted[0])

    default_limit = 40
    default_offset = 0

    try:
        default_limit = int(request.GET["limit"])
    except (KeyError, ValueError):
        pass

    try:
        default_offset = int(request.GET["offset"])
    except (KeyError, ValueError):
        pass

    return included_select_options, default_limit, default_offset
