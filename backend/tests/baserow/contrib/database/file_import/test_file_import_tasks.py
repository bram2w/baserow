import pytest
from pyinstrument import Profiler
from baserow.core.exceptions import UserNotInGroup

from baserow.core.jobs.tasks import run_async_job
from baserow.core.jobs.constants import (
    JOB_FINISHED,
)


@pytest.mark.django_db(transaction=True)
def test_run_file_import_task(data_fixture):

    user = data_fixture.create_user()
    table = data_fixture.create_database_table()

    job = data_fixture.create_file_import_job(user=user, table=table)

    with pytest.raises(UserNotInGroup):
        run_async_job(job.id)

    job = data_fixture.create_file_import_job()
    table = job.table

    run_async_job(job.id)

    job.refresh_from_db()
    assert job.state == JOB_FINISHED
    assert job.progress_percentage == 100

    model = table.get_model()
    rows = model.objects.all()

    assert len(rows) == 5


@pytest.mark.django_db(transaction=True)
@pytest.mark.disabled_in_ci
# You must add --run-disabled-in-ci -s to pytest to run this test, you can do this in
# intellij by editing the run config for this test and adding --run-disabled-in-ci -s
# to additional args.
def test_run_file_import_task_big_data(data_fixture):

    row_count = 100_000

    job = data_fixture.create_file_import_job(column_count=100, row_count=row_count)
    table = job.table

    profiler = Profiler()
    profiler.start()
    run_async_job(job.id)
    profiler.stop()

    job.refresh_from_db()
    assert job.state == JOB_FINISHED
    assert job.progress_percentage == 100

    model = table.get_model()
    rows = model.objects.all()
    assert rows.count() == row_count

    print(profiler.output_text(unicode=True, color=True, show_all=True))
