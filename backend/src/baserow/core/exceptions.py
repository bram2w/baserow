class UserNotInGroupError(Exception):
    """Raised when the user doesn't have access to the related group."""

    def __init__(self, user=None, group=None, *args, **kwargs):
        if user and group:
            super().__init__(f'User {user} doesn\'t belong to group {group}.', *args,
                             **kwargs)
        else:
            super().__init__('The user doesn\'t belong to the group', *args, **kwargs)


class ApplicationAlreadyRegistered(Exception):
    pass


class ApplicationTypeDoesNotExist(Exception):
    pass
