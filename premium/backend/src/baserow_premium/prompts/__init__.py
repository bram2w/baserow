from functools import cache
from importlib.resources import read_text


@cache
def get_generate_formula_prompt():
    return read_text("baserow_premium.prompts", "generate_formula.prompt")
