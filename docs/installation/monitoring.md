# Monitoring your Baserow server 

Baserow can be configured to ship logs, metrics and traces using
the [Open Telemetry standard](https://opentelemetry.io/). You can use these to monitor
your Baserow instance.

Enable this by setting the env var `BASEROW_ENABLE_OTEL=true` and then depending on
where you want to send telemetry set the
appropriate [OTEL env vars](https://opentelemetry.io/docs/reference/specification/sdk-environment-variables/#general-sdk-configuration).
You probably want to set `OTEL_EXPORTER_OTLP_ENDPOINT` also.
> In our default docker-compose files we have only added passthroughs for the following
> OTEL specific env vars.
> * OTEL_EXPORTER_OTLP_ENDPOINT
> * OTEL_RESOURCE_ATTRIBUTES
>
> If you want to use more, you need to edit the compose files
> yourself and add the env var passthroughs you need.

By default, Baserow will send the following telemetry:

- Baserow application logging. 
- Some basic metrics.
- Various spans over some of our critical functions and handler methods.
- Automatic instrumentation provided by OTEL libraries for:
    - S3 usage by the `botocore` library
    - SQL queries
    - Redis queries
    - HTTP queries
    - Celery tasks
    - Django requests/responses

