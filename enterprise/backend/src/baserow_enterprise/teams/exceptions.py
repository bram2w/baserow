class UserNotInTeam(Exception):
    """Raised when the user doesn't have access to the related team."""

    def __init__(self, user=None, team=None, *args, **kwargs):
        if user and team:
            super().__init__(
                f"User {user} doesn't belong to team {team}.", *args, **kwargs
            )
        else:
            super().__init__("The user doesn't belong to the team", *args, **kwargs)


class UnsupportedSubjectType(Exception):
    """Raised when a subject is invited to a team, and we don't support its type."""

    def __init__(self, subject_type: str, *args, **kwargs):
        if subject_type:
            super().__init__(
                f"Type {subject_type} is not a supported team subject type.",
                *args,
                **kwargs,
            )
        else:
            super().__init__("The subject type is not supported.", *args, **kwargs)
