from baserow.config.settings.base import *


INSTALLED_APPS = INSTALLED_APPS + ['{{ cookiecutter.project_module }}']
