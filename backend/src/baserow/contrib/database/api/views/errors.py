from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND


ERROR_VIEW_DOES_NOT_EXIST = (
    'ERROR_VIEW_DOES_NOT_EXIST',
    HTTP_404_NOT_FOUND,
    'The requested view does not exist.'
)
ERROR_VIEW_FILTER_DOES_NOT_EXIST = (
    'ERROR_VIEW_FILTER_DOES_NOT_EXIST',
    HTTP_404_NOT_FOUND,
    'The view filter does not exist.'
)
ERROR_VIEW_FILTER_NOT_SUPPORTED = (
    'ERROR_VIEW_FILTER_NOT_SUPPORTED',
    HTTP_400_BAD_REQUEST,
    'Filtering is not supported for the view type.'
)
ERROR_VIEW_FILTER_TYPE_DOES_NOT_EXIST = (
    'ERROR_VIEW_FILTER_TYPE_DOES_NOT_EXIST',
    HTTP_400_BAD_REQUEST,
    'The view filter type {e.type_name} doesn\'t exist.'
)
ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD = (
    'ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD',
    HTTP_400_BAD_REQUEST,
    'The filter {e.filter_type} is not compatible with field type {e.field_type}.'
)
ERROR_VIEW_SORT_DOES_NOT_EXIST = (
    'ERROR_VIEW_SORT_DOES_NOT_EXIST',
    HTTP_404_NOT_FOUND,
    'The view sort does not exist.'
)
ERROR_VIEW_SORT_NOT_SUPPORTED = (
    'ERROR_VIEW_SORT_NOT_SUPPORTED',
    HTTP_400_BAD_REQUEST,
    'Sorting is not supported for the view type.'
)
ERROR_VIEW_SORT_FIELD_ALREADY_EXISTS = (
    'ERROR_VIEW_SORT_FIELD_ALREADY_EXISTS',
    HTTP_400_BAD_REQUEST,
    'A sort with the field already exists in the view.'
)
ERROR_VIEW_SORT_FIELD_NOT_SUPPORTED = (
    'ERROR_VIEW_SORT_FIELD_NOT_SUPPORTED',
    HTTP_400_BAD_REQUEST,
    'The field does not support view sorting.'
)
