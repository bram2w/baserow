from django.db import models


class FormulaField(models.TextField):
    """
    A formula field contains the text value of a runtime formula like:
    - concat("test:", get("page_parameter.id"), "-")
    - get("data_source.Product.id")

    For now it's just a text field but we can add layer of validation later.
    """
