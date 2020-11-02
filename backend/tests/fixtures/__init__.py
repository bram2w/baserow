from faker import Faker

from .user import UserFixtures
from .group import GroupFixtures
from .application import ApplicationFixtures
from .table import TableFixtures
from .view import ViewFixtures
from .field import FieldFixtures
from .token import TokenFixtures


class Fixtures(UserFixtures, GroupFixtures, ApplicationFixtures, TableFixtures,
               ViewFixtures, FieldFixtures, TokenFixtures):
    fake = Faker()
