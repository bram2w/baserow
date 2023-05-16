from celery_singleton.backends import RedisBackend
from django_redis import get_redis_connection


class RedisBackendForSingleton(RedisBackend):
    def __init__(self, *args, **kwargs):
        """
        Use the existing redis connection instead of creating a new one.
        """

        self.redis = get_redis_connection("default")
