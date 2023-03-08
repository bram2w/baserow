from baserow.core.telemetry.telemetry import setup_telemetry


def post_fork(server, worker):
    setup_telemetry(add_django_instrumentation=True)
