from .base import *  # noqa: F403, F401


DEBUG = True

try:
    from .local import *  # noqa: F403, F401
except ImportError:
    pass
