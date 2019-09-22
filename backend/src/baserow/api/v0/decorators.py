from collections import defaultdict

from django.utils.encoding import force_text

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.request import Request


def map_exceptions(exceptions):
    """
    This decorator simplifies mapping specific exceptions to a standard api response.

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


def validate_body(serializer_class):
    """
    This decorator can validate the request body using a serializer. If the body is
    valid it will add the data to the kwargs. If not it will raise an APIException with
    structured details about what is wrong.

    Example:
        class LoginSerializer(serializers.Serializer):
            username = serializers.EmailField()
            password = serializers.CharField()

        @validate_body(LoginSerializer)
        def post(self, request):
           raise SomeException('This is a test')

        HTTP/1.1 400
        {
          "error": "ERROR_REQUEST_BODY_VALIDATION",
          "detail": {
            "username": [
              {
                "error": "This field is required.",
                "code": "required"
              }
            ]
          }
        }

    :param serializer_class: The serializer that must be used for validating.
    :type serializer_class: Serializer
    """

    def validate_decorator(func):
        def func_wrapper(*args, **kwargs):
            # Check if the request
            if len(args) < 2 or not isinstance(args[1], Request):
                raise ValueError('There must be a request in the kwargs.')

            request = args[1]
            serializer = serializer_class(data=request.data)
            if not serializer.is_valid():
                # Create a serialized detail on why the validation failed.
                detail = defaultdict(list)
                for key, errors in serializer.errors.items():
                    for error in errors:
                        detail[key].append({
                            'error': force_text(error),
                            'code': error.code
                        })

                exc = APIException({
                    'error': 'ERROR_REQUEST_BODY_VALIDATION',
                    'detail': detail
                })
                exc.status_code = 400
                raise exc

            # We do not want to override already existing data value in the kwargs.
            if 'data' in kwargs:
                raise ValueError('The data attribute is already in the kwargs.')

            kwargs['data'] = serializer.data
            return func(*args, **kwargs)
        return func_wrapper
    return validate_decorator
