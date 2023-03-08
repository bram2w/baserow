from typing import List

from django.contrib.auth.models import AbstractUser

from baserow.core.models import Group
from baserow.core.registries import SubjectType

from .models import Token


class TokenSubjectType(SubjectType):

    type = "core.Token"
    model_class = Token

    def are_in_group(self, subjects: List[Token], group: Group) -> List[bool]:
        """
        Check whether the given subjects are member of the given group.
        """

        token_ids_in_group = set(
            Token.objects.filter(
                id__in=[s.id for s in subjects], group=group
            ).values_list("id", flat=True)
        )

        return [s.id in token_ids_in_group for s in subjects]

    def get_serializer(self, model_instance, **kwargs):
        from baserow.contrib.database.api.tokens.serializers import TokenSerializer

        return TokenSerializer(model_instance, **kwargs)

    def get_users_included_in_subject(self, subject: Token) -> List[AbstractUser]:
        return []
