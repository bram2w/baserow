from django.core.signals import setting_changed
from django.dispatch import receiver

from cachalot.settings import cachalot_settings


@receiver(setting_changed)
def reload_settings(sender, **kwargs):
    cachalot_settings.reload()
