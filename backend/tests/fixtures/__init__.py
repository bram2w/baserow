from faker import Faker

from .user import UserFixtures
from .group import GroupFixtures
from .application import ApplicationFixtures


class Fixtures(UserFixtures, GroupFixtures, ApplicationFixtures):
    fake = Faker()
