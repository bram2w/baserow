from celery.signals import worker_process_init

from baserow.core.telemetry.telemetry import setup_logging, setup_telemetry


@worker_process_init.connect
def initialize_otel(**kwargs):
    setup_telemetry(add_django_instrumentation=False)
    setup_logging()
