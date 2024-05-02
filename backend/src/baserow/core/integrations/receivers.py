from django.dispatch import receiver

from baserow.core.signals import application_created


@receiver(application_created)
def execute_integration_post_template_install_hooks(
    sender, application, user, **kwargs
):
    if application.installed_from_template is not None:
        for integration in application.integrations.all():
            integration.get_type().after_template_install(user, integration.specific)
