from baserow.core.models import Group, GroupUser


class GroupFixtures:
    def create_group(self, **kwargs):
        user = kwargs.pop('user', None)
        users = kwargs.pop('users', [])

        if user:
            users.insert(0, user)

        if 'name' not in kwargs:
            kwargs['name'] = self.fake.name()

        group = Group.objects.create(**kwargs)

        for user in users:
            self.create_user_group(group=group, user=user, order=0)

        return group

    def create_user_group(self, **kwargs):
        if 'group' not in kwargs:
            kwargs['group'] = self.create_group()

        if 'user' not in kwargs:
            kwargs['user'] = self.create_user()

        if 'order' not in kwargs:
            kwargs['order'] = 0

        return GroupUser.objects.create(**kwargs)
