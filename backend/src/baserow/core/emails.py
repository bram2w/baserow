from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext as _
from django.db import transaction


class BaseEmailMessage(EmailMultiAlternatives):
    """
    The base email message class can be used to create reusable email classes for
    each email. The template_name is rendered to a string and attached as html
    alternative. This content is automatically converted to plain text. The get_context
    method can be extended to add additional context variables while rendering the
    template.

    Example:
        class TestEmail(BaseEmailMessage):
            subject = 'Example subject'
            template_name = 'baserow/core/example.html'

        email = TestEmail(['test@localhost'])
        email.send()
    """

    subject = None
    template_name = None

    def __init__(self, to, from_email=None):
        if not from_email:
            from_email = self.get_from_email()

        subject = self.get_subject()
        template_name = self.get_template_name()
        context = self.get_context()
        html_content = render_to_string(template_name, context)

        try:
            body_start_index = html_content.index("<body>")
            body_end_index = html_content.index("</body>")
            html_content = html_content[body_start_index:body_end_index]
        except ValueError:
            pass

        text_content = strip_tags(html_content)

        super().__init__(
            subject=subject, body=text_content, from_email=from_email, to=to
        )
        self.attach_alternative(html_content, "text/html")

    def get_context(self):
        return {
            "public_backend_hostname": settings.PUBLIC_BACKEND_HOSTNAME,
            "public_backend_url": settings.PUBLIC_BACKEND_URL,
            "public_web_frontend_hostname": settings.PUBLIC_WEB_FRONTEND_HOSTNAME,
            "public_web_frontend_url": settings.PUBLIC_WEB_FRONTEND_URL,
        }

    def get_from_email(self):
        return settings.FROM_EMAIL

    def get_subject(self):
        if not self.subject:
            raise NotImplementedError("The subject must be implement.")
        return self.subject

    def get_template_name(self):
        if not self.template_name:
            raise NotImplementedError("The template_name must be implement.")
        return self.template_name

    def send(self, fail_silently=False):
        s = super()
        transaction.on_commit(lambda: s.send(fail_silently))


class GroupInvitationEmail(BaseEmailMessage):
    template_name = "baserow/core/group_invitation.html"

    def __init__(self, invitation, public_accept_url, *args, **kwargs):
        self.public_accept_url = public_accept_url
        self.invitation = invitation
        super().__init__(*args, **kwargs)

    def get_subject(self):
        return _("%(by)s invited you to %(group_name)s - Baserow",) % {
            "by": self.invitation.invited_by.first_name,
            "group_name": self.invitation.group.name,
        }

    def get_context(self):
        context = super().get_context()
        context.update(
            invitation=self.invitation, public_accept_url=self.public_accept_url
        )
        return context
