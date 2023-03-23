from django.core.exceptions import ValidationError

import pytest

from baserow.contrib.builder.pages.validators import (
    path_params_validation,
    path_validation,
)


def test_page_path_validation():
    try:
        path_validation("/test/test/:id")
    except ValidationError:
        pytest.fail("Should have not raised for the valid path")

    with pytest.raises(ValidationError):
        path_validation("no/slash/at/the/start")

    with pytest.raises(ValidationError):
        path_validation("\r")

    with pytest.raises(ValidationError):
        path_validation("path with spaces")


def test_path_params_validation():
    try:
        path_params_validation({"test": {"param_type": "text"}})
    except ValidationError:
        pytest.fail("Should have not raised for valid path param")

    with pytest.raises(ValidationError):
        path_params_validation({"^test": {"param_type": "text"}})

    with pytest.raises(ValidationError):
        path_params_validation(
            {"test": {"param_type": "text"}, "^test": {"param_type": "text"}}
        )

    with pytest.raises(ValidationError):
        path_params_validation({" ": {"param_type": "text"}})

    with pytest.raises(ValidationError):
        path_params_validation({"test**11": {"param_type": "text"}})
