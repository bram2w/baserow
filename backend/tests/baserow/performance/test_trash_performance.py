import pytest
from pyinstrument import Profiler

from baserow.contrib.database.management.commands.fill_table import fill_table
from baserow.core.models import TrashEntry
from baserow.core.trash.handler import TrashHandler
from baserow.test_utils.helpers import setup_interesting_test_table


@pytest.mark.django_db
@pytest.mark.slow
# You must add --runslow -s to pytest to run this test, you can do this in intellij by
# editing the run config for this test and adding --runslow -s to additional args.
def test_deleting_many_of_rows_is_fast(data_fixture):

    table, user, row, _ = setup_interesting_test_table(data_fixture)
    count = 1000
    fill_table(count, table)

    model = table.get_model()
    for row in model.objects.all():
        TrashHandler.trash(
            user, table.database.group, table.database, row, parent_id=table.id
        )

    TrashEntry.objects.update(should_be_permanently_deleted=True)

    assert model.objects.all().count() == 0
    assert model.trash.all().count() == count + 2
    assert TrashEntry.objects.count() == count + 2

    profiler = Profiler()
    profiler.start()
    TrashHandler.permanently_delete_marked_trash()
    profiler.stop()
    # Add -s also the the additional args to see the profiling output!
    # As of 22/06/2021 on a 5900X the profiler output showed 0.82 seconds to
    # perm delete these 1000 rows.
    # As of 23/08/2021 on a 5900X the profiler output showed 1.849 seconds to
    # perm delete these 1000 rows after the change was made to lookup trash entries
    # one by one, see https://gitlab.com/bramw/baserow/-/issues/595.
    print(profiler.output_text(unicode=True, color=True))
