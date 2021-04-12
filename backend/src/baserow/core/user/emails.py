from django.conf import settings
from django.utils.translation import gettext as _

from baserow.core.emails import BaseEmailMessage


class ResetPasswordEmail(BaseEmailMessage):
    subject = _("Reset password - Baserow")
    template_name = "baserow/core/user/reset_password.html"

    def __init__(self, user, reset_url, *args, **kwargs):
        self.reset_url = reset_url
        self.user = user
        super().__init__(*args, **kwargs)

    def get_context(self):
        context = super().get_context()
        context.update(
            user=self.user,
            reset_url=self.reset_url,
            expire_hours=settings.RESET_PASSWORD_TOKEN_MAX_AGE / 60 / 60,
        )
        return context
