# Please keep in sync with the web-frontend version of this constant found in
# web-frontend/modules/database/utils/constants.js
RESERVED_BASEROW_FIELD_NAMES = {"id", "order"}
# This is an internal only field that allows upserting select options with a specific
# pk.
UPSERT_OPTION_DICT_KEY = "upsert_id"

# WARNING: these values are prone to SQL injection
# lowercase serializers.BooleanField.TRUE_VALUES + "checked" keyword
# fmt: off
BASEROW_BOOLEAN_FIELD_TRUE_VALUES = [
    't', 'T',
    'y', 'Y', 'yes', 'Yes', 'YES',
    'true', 'True', 'TRUE',
    'on', 'On', 'ON',
    '1', 1,
    "checked",
    True
]
# lowercase serializers.BooleanField.FALSE_VALUES + "unchecked" keyword
# fmt: off
BASEROW_BOOLEAN_FIELD_FALSE_VALUES = [
    'f', 'F',
    'n', 'N', 'no', 'No', 'NO',
    'false', 'False', 'FALSE',
    'off', 'Off', 'OFF',
    '0', 0, 0.0,
    "unchecked",
    False
]
