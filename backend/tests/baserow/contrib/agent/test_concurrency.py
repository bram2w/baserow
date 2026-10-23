from concurrent.futures import ThreadPoolExecutor
from threading import Event
from time import monotonic, sleep

from django.db import connection, connections, transaction

import pytest

from baserow.contrib.agent.service import AgentService
from baserow.core.actions import UpdateApplicationActionType
from baserow.core.handler import CoreHandler
from baserow.core.models import Application


@pytest.mark.django_db(transaction=True)
def test_configuration_update_and_application_rename_are_serialized(data_fixture):
    user = data_fixture.create_user()
    agent = data_fixture.create_agent_application(
        user=user, name="Original name", instructions="Original instructions"
    )
    rename_locked = Event()
    release_rename = Event()
    configuration_connected = Event()
    configuration_pid = []

    def rename_application():
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET statement_timeout = '10s'")
            with transaction.atomic():
                # The generic application PATCH locks its parent before its action.
                application = (
                    CoreHandler()
                    .get_application(
                        agent.id,
                        base_queryset=Application.objects.select_for_update(
                            of=("self",)
                        ),
                    )
                    .specific
                )
                rename_locked.set()
                assert release_rename.wait(10), "The rename was never released"
                UpdateApplicationActionType.do(user, application, name="Renamed agent")
        finally:
            connections.close_all()

    def update_configuration():
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET statement_timeout = '10s'")
                cursor.execute("SELECT pg_backend_pid()")
                configuration_pid.append(cursor.fetchone()[0])
                configuration_connected.set()
            AgentService().update_configuration(
                user, agent.id, instructions="Updated instructions"
            )
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        rename = executor.submit(rename_application)
        try:
            assert rename_locked.wait(10)
            configuration = executor.submit(update_configuration)
            assert configuration_connected.wait(10)
            deadline = monotonic() + 5
            blocked = False
            while monotonic() < deadline and not configuration.done():
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT cardinality(pg_blocking_pids(%s))", configuration_pid
                    )
                    blocked = cursor.fetchone()[0] > 0
                if blocked:
                    break
                sleep(0.01)
            assert blocked, "The configuration update did not wait for the rename"
        finally:
            release_rename.set()
        rename.result(timeout=10)
        configuration.result(timeout=10)

    agent.refresh_from_db()
    assert (agent.name, agent.instructions) == ("Renamed agent", "Updated instructions")
