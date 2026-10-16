import re
from pathlib import Path

import pytest

from baserow.core.user_templates.constants import USER_TEMPLATE_ICONS

FRONTEND_ICONS_PATH = (
    Path(__file__).resolve().parents[5]
    / "web-frontend"
    / "modules"
    / "core"
    / "utils"
    / "templateIcons.js"
)


@pytest.mark.skipif(
    not FRONTEND_ICONS_PATH.exists(),
    reason="The web-frontend isn't next to the backend, for example in the backend "
    "CI image.",
)
def test_frontend_template_icons_match_the_backend():
    source = FRONTEND_ICONS_PATH.read_text()
    array = re.search(r"TEMPLATE_ICONS = \[(.*?)\]", source, re.S)

    assert array, "TEMPLATE_ICONS not found in templateIcons.js"
    assert tuple(re.findall(r"'([^']+)'", array.group(1))) == USER_TEMPLATE_ICONS
