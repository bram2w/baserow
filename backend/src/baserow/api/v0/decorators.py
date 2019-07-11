from rest_framework import status
from rest_framework.exceptions import APIException


def map_exceptions(exceptions):
    """This decorator easily maps specific exceptions to a standard api response.

    Example:
      @map_exceptions({ SomeException: 'ERROR_1' })
      def get(self, request):
           raise SomeException('This is a test')

      HTTP/1.1 400
      {
        "error": "ERROR_1",
        "detail": "This is a test"
      }

    Example 2:
      @map_exceptions({ SomeException: ('ERROR_1', 404, 'Other message') })
      def get(self, request):
           raise SomeException('This is a test')

      HTTP/1.1 404
      {
        "error": "ERROR_1",
        "detail": "Other message"
      }
    """
    def map_exceptions_decorator(func):
        def func_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except tuple(exceptions.keys()) as e:
                value = exceptions.get(e.__class__)
                status_code = status.HTTP_400_BAD_REQUEST
                detail = str(e)

                if isinstance(value, str):
                    error = value
                if isinstance(value, tuple):
                    error = value[0]
                    if len(value) > 1 and value[1] is not None:
                        status_code = value[1]
                    if len(value) > 2 and value[2] is not None:
                        detail = value[2]

                exc = APIException({
                    'error': error,
                    'detail': detail
                })
                exc.status_code = status_code

                raise exc
        return func_wrapper
    return map_exceptions_decorator
