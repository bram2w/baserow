import os

from opentelemetry.sdk.trace import TracerProvider

from baserow.core.telemetry.env_overrides_parser import get_sampler_overrides_from_str

BASEROW_CUSTOM_OTEL_SAMPLER_ENV_VAR_NAME = "OTEL_PER_MODULE_SAMPLER_OVERRIDES"


class DifferentSamplerPerLibraryTracerProvider(TracerProvider):
    """
    This TracerProvider allows using different samplers for different modules doing
    instrumentation.

    This is useful for example if you want to configure you app to always instrument
    spans from instrumentation library A, but otherwise use the default sampler.

    It is configured using the OTEL_PER_MODULE_SAMPLER_OVERRIDES environment variable
    being set to a string of the following format:
     module.name.something=sampler,other.module=other-sampler-with-param@0.5

    For example you could set OTEL_PER_MODULE_SAMPLER_OVERRIDES=
    "opentelemetry.instrumentation.celery=always_on,
     opentelemetry.instrumentation.django=always_on"

    Which would result in OTEL always sampling any spans produced by the celery and
    django otel instrumentation libraries. In effect meaning you will get 100% of
    the root spans showing every request and celery task run.

    The supported sampler strings are:
        * "always_on"
        * "always_off"
        * "parentbased_always_on"
        * "parentbased_always_off"
        * "traceidratio@{float}"
        * "parentbased_traceidratio@{float}"

    And correspond to the OTEL samplers with the same names, see
    https://opentelemetry-python.readthedocs.io/en/latest/sdk/trace.sampling.html for
    more details.
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        self.default_sampler_override_per_instrumented_module_name = (
            get_sampler_overrides_from_str(
                os.getenv(BASEROW_CUSTOM_OTEL_SAMPLER_ENV_VAR_NAME, "")
            )
        )
        super().__init__(*args, **kwargs)
        self.default_sampler = self.sampler

    def get_tracer(self, instrumenting_module_name: str, *args, **kwargs):
        self.sampler = self.default_sampler_override_per_instrumented_module_name.get(
            instrumenting_module_name, self.default_sampler
        )
        return super().get_tracer(instrumenting_module_name, *args, **kwargs)
