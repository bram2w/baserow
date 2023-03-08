from faker import Faker

from .airtable import AirtableFixtures
from .application import ApplicationFixtures
from .auth_provider import AuthProviderFixtures
from .field import FieldFixtures
from .file_import import FileImportFixtures
from .group import GroupFixtures
from .job import JobFixtures
from .page import PageFixtures
from .row import RowFixture
from .settings import SettingsFixtures
from .snapshots import SnapshotFixtures
from .table import TableFixtures
from .template import TemplateFixtures
from .token import TokenFixtures
from .user import UserFixtures
from .user_file import UserFileFixtures
from .view import ViewFixtures
from .webhook import TableWebhookFixture


class Fixtures(
    SettingsFixtures,
    UserFixtures,
    UserFileFixtures,
    GroupFixtures,
    ApplicationFixtures,
    TableFixtures,
    ViewFixtures,
    FieldFixtures,
    TokenFixtures,
    TemplateFixtures,
    RowFixture,
    TableWebhookFixture,
    AirtableFixtures,
    JobFixtures,
    FileImportFixtures,
    SnapshotFixtures,
    AuthProviderFixtures,
    PageFixtures,
):
    fake = Faker()
