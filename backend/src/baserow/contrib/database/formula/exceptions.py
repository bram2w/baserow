from django.conf import settings

from loguru import logger


class BaserowFormulaException(Exception):
    pass


def formula_exception_handler(e):
    """
    Attempts to send formula errors to sentry in non debug mode and logs errors. In
    debug mode raises the exception.

    :param e: The exception to report.
    """

    if settings.DEBUG or settings.TESTS:
        # We want to see any issues immediately in debug mode.
        raise e
    try:
        from sentry_sdk import capture_exception

        capture_exception(e)
    except ImportError:
        pass
    logger.error(
        f"Formula related error occurred: {e}. Please send this error to the baserow "
        f"developers at https://baserow.io/contact."
    )
    logger.exception(e)
