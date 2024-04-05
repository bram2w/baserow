from django.db import models

from baserow.contrib.database.fields.models import Field
from baserow.core.formula.field import FormulaField as ModelFormulaField


class AIField(Field):
    ai_generative_ai_type = models.CharField(max_length=32, null=True)
    ai_generative_ai_model = models.CharField(max_length=32, null=True)
    ai_prompt = ModelFormulaField(default="")
