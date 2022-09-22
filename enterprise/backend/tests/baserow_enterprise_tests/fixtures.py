class EnterpriseFixtures:
    def create_user(self, *args, **kwargs):
        user = super().create_user(*args, **kwargs)
        return user
