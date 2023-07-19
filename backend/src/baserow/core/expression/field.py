from django.db import models


class ExpressionField(models.TextField):
    """
    An expression that can reference a data source, a formula or a plain value.
    """
