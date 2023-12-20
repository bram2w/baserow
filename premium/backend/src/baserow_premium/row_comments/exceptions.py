from baserow_premium.row_comments.models import RowComment


class InvalidRowCommentException(Exception):
    pass


class RowCommentDoesNotExist(RowComment.DoesNotExist):
    pass


class UserNotRowCommentAuthorException(Exception):
    pass


class InvalidRowCommentMentionException(Exception):
    pass


class InvalidRowsCommentNotificationModeException(ValueError):
    pass
