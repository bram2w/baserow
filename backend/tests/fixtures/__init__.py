from faker import Faker

from .user import UserFixtures
from .group import GroupFixtures
from .application import ApplicationFixtures
from .table import TableFixtures
from .view import ViewFixtures


class Fixtures(UserFixtures, GroupFixtures, ApplicationFixtures, TableFixtures,
               ViewFixtures):
    fake = Faker()
