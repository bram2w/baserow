from faker import Faker

from .user import UserFixtures
from .group import GroupFixtures
from .application import ApplicationFixtures
from .table import TableFixtures


class Fixtures(UserFixtures, GroupFixtures, ApplicationFixtures, TableFixtures):
    fake = Faker()
