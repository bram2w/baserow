from .utils import (
    map_exceptions as map_exceptions_utility,
    get_request,
    validate_data,
    validate_data_custom_fields,
)
from .exceptions import RequestBodyValidationException


def map_exceptions(exceptions):
    """
    This decorator simplifies mapping specific exceptions to a standard api response.
    Note that this decorator uses the map_exception function from baserow.api.utils
    which has the same name and basically does the same only this works in the form of
    a decorator.

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
            with map_exceptions_utility(exceptions):
                return func(*args, **kwargs)

        return func_wrapper

    return map_exceptions_decorator


def validate_body(serializer_class, partial=False):
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
    :param partial: Whether partial data passed to the serializer is considered valid.
    :type serializer_class: Serializer
    :raises ValueError: When the `data` attribute is already in the kwargs. This
        decorator tries to add the `data` attribute, but cannot do that if it is
        already present.
    """

    def validate_decorator(func):
        def func_wrapper(*args, **kwargs):
            request = get_request(args)

            if "data" in kwargs:
                raise ValueError("The data attribute is already in the kwargs.")

            kwargs["data"] = validate_data(serializer_class, request.data, partial)
            return func(*args, **kwargs)

        return func_wrapper

    return validate_decorator


def validate_body_custom_fields(
    registry, base_serializer_class=None, type_attribute_name="type"
):
    """
    This decorator can validate the request data dynamically using the generated
    serializer that belongs to the type instance. Based on a provided
    type_attribute_name it will check the request data for a type identifier and based
    on that value it will load the type instance from the registry. With that type
    instance we know with which fields to build a serializer with that will be used.

    :param registry: The registry object where to get the type instance from.
    :type registry: Registry
    :param base_serializer_class: The base serializer class that will be used when
        generating the serializer.
    :type base_serializer_class: ModelSerializer
    :param type_attribute_name: The attribute name containing the type value in the
        request data.
    :type type_attribute_name: str
    :raises RequestBodyValidationException: When the `type` is not provided.
    :raises ValueError: When the `data` attribute is already in the kwargs. This
        decorator tries to add the `data` attribute, but cannot do that if it is
        already present.
    """

    def validate_decorator(func):
        def func_wrapper(*args, **kwargs):
            request = get_request(args)
            type_name = request.data.get(type_attribute_name)

            if not type_name:
                # If the type name isn't provided in the data we will raise a machine
                # readable validation error.
                raise RequestBodyValidationException(
                    {
                        type_attribute_name: [
                            {"error": "This field is required.", "code": "required"}
                        ]
                    }
                )

            if "data" in kwargs:
                raise ValueError("The data attribute is already in the kwargs.")

            kwargs["data"] = validate_data_custom_fields(
                type_name,
                registry,
                request.data,
                base_serializer_class=base_serializer_class,
                type_attribute_name=type_attribute_name,
            )
            return func(*args, **kwargs)

        return func_wrapper

    return validate_decorator


def allowed_includes(*allowed):
    """
    A view method decorator that checks which allowed includes are in the GET
    parameters of the request. The allowed arguments are going to be added to the
    view method kwargs and if they are in the `include` GET parameter the value will
    be True.

    Imagine this request:

    # GET /page/?include=cars,unrelated_stuff,bikes
    @allowed_includes('cars', 'bikes', 'planes')
    def get(request, cars, bikes, planes):
        cars >> True
        bikes >> True
        planes >> False

    # GET /page/?include=planes
    @allowed_includes('cars', 'bikes', 'planes')
    def get(request, cars, bikes, planes):
        cars >> False
        bikes >> False
        planes >> True

    :param allowed: Should have all the allowed include values.
    :type allowed: list
    """

    def validate_decorator(func):
        def func_wrapper(*args, **kwargs):
            request = get_request(args)
            raw_include = request.GET.get("include", None)
            includes = raw_include.split(",") if raw_include else []

            for include in allowed:
                kwargs[include] = include in includes

            return func(*args, **kwargs)

        return func_wrapper

    return validate_decorator
