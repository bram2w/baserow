from faker import Faker

from .user import UserFixtures
from .group import GroupFixtures


class Fixtures(UserFixtures, GroupFixtures):
    fake = Faker()
