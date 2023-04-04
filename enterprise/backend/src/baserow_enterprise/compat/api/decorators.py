import functools

from rest_framework.exceptions import APIException


def map_compat_codes(error_code_map: dict[str, str]):
    """
    A decorator for compatibility views.

    Given an `error_code_map` such as:
        {
            "ERROR_WORKSPACE_DOES_NOT_EXIST": "ERROR_GROUP_DOES_NOT_EXIST"
        }

    When the compatibility view's base view raises an error code of
    `ERROR_WORKSPACE_DOES_NOT_EXIST`, we'll manipulate the `APIException`
    so that instead, we raise `ERROR_GROUP_DOES_NOT_EXIST`.
    """

    def outer(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except APIException as e:
                try:
                    raised_error_code = e.detail["error"]
                except TypeError:
                    # APIException subclasses can just have a string
                    # `e.detail`, so `error` will raise a `TypeError`.
                    raise e
                for error_code, compat_error_code in error_code_map.items():
                    if raised_error_code == error_code:
                        e.detail["error"] = compat_error_code
                        print(f"Changed {error_code} to {compat_error_code}")
                raise e

        return inner

    return outer
