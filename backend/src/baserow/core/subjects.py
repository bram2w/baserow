from typing import List

from django.contrib.auth.models import AbstractUser

from baserow.core.models import Group, GroupUser, User
from baserow.core.registries import SubjectType
from baserow_enterprise.api.role.serializers import SubjectUserSerializer


class UserSubjectType(SubjectType):

    type = "auth.User"
    model_class = User

    def is_in_group(self, subject_id: int, group: Group) -> bool:
        return GroupUser.objects.filter(
            user_id=subject_id,
            group=group,
            user__profile__to_be_deleted=False,
            user__is_active=True,
        ).exists()

    def get_serializer(self, model_instance, **kwargs):
        return SubjectUserSerializer(model_instance, **kwargs)

    def get_associated_users(self, user: AbstractUser) -> List[AbstractUser]:
        return [user]
