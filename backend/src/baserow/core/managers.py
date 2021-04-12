from django.db import models


class GroupQuerySet(models.QuerySet):
    def of_user(self, user):
        return self.filter(users__exact=user).order_by("groupuser__order")
