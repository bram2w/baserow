import logging

# disable annoying info messages like:
# xmlschema.include_schema:1250- Resource 'XMLSchema.xsd' is already loaded
logging.getLogger("xmlschema").setLevel(logging.WARNING)
