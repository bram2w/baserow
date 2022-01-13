from rest_framework.pagination import LimitOffsetPagination


class GalleryLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 100
