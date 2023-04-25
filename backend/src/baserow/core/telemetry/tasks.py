from celery.signals import task_prerun, worker_process_init
from opentelemetry import baggage, context

from baserow.core.telemetry.telemetry import setup_logging, setup_telemetry
from baserow.core.telemetry.utils import otel_is_enabled

TASK_NAME_KEY = "celery.task_name"


@worker_process_init.connect
def initialize_otel(**kwargs):
    setup_telemetry(add_django_instrumentation=False)
    setup_logging()


@task_prerun.connect
def before_task(task_id, task, *args, **kwargs):
    if otel_is_enabled():
        context.attach(baggage.set_baggage(TASK_NAME_KEY, task.name))
