from opentelemetry.sdk.trace.sampling import (
    ALWAYS_OFF,
    ALWAYS_ON,
    DEFAULT_OFF,
    DEFAULT_ON,
    ParentBasedTraceIdRatio,
)

from baserow.core.telemetry.env_overrides_parser import get_sampler_overrides_from_str
from baserow.core.telemetry.sampling import ForcableTraceIdRatioBased


def test_invalid_sampler_strings():
    assert get_sampler_overrides_from_str("") == {}
    assert get_sampler_overrides_from_str("123.2132") == {}
    assert get_sampler_overrides_from_str("[]") == {}
    assert get_sampler_overrides_from_str("{}}") == {}
    assert get_sampler_overrides_from_str("false") == {}
    assert get_sampler_overrides_from_str("invalid") == {}
    assert get_sampler_overrides_from_str("invalid,invalid,invalid=10") == {}
    assert get_sampler_overrides_from_str("invalid,invalid2,invalid3=10") == {}
    assert get_sampler_overrides_from_str("my.module=traceidratio") == {}
    assert get_sampler_overrides_from_str("my.module=parentbased_traceidratio") == {}
    assert get_sampler_overrides_from_str("my.module=traceidratio@") == {}
    assert get_sampler_overrides_from_str("my.module=parentbased_traceidratio@") == {}
    assert get_sampler_overrides_from_str("my.module=traceidratio@a") == {}
    assert get_sampler_overrides_from_str("my.module=parentbased_traceidratio@a") == {}
    assert get_sampler_overrides_from_str("my.module=traceidratio@-0.1") == {}
    assert (
        get_sampler_overrides_from_str("my.module=parentbased_traceidratio@-0.1") == {}
    )
    assert get_sampler_overrides_from_str("my.module=traceidratio@1.1") == {}
    assert (
        get_sampler_overrides_from_str("my.module=parentbased_traceidratio@1.1") == {}
    )


def test_valid_sampler_strings():
    assert get_sampler_overrides_from_str("my.module=always_on") == {
        "my.module": ALWAYS_ON
    }
    assert get_sampler_overrides_from_str("my.module=always_off") == {
        "my.module": ALWAYS_OFF
    }
    assert get_sampler_overrides_from_str("my.module=parentbased_always_on") == {
        "my.module": DEFAULT_ON
    }
    assert get_sampler_overrides_from_str("my.module=parentbased_always_off") == {
        "my.module": DEFAULT_OFF
    }


def test_valid_sampler_with_args():
    for_trace_id = get_sampler_overrides_from_str("my.module=traceidratio@0.4")
    assert type(for_trace_id["my.module"]) is ForcableTraceIdRatioBased
    assert for_trace_id["my.module"].rate == 0.4
    for_parent_trace_id = get_sampler_overrides_from_str(
        "my.module=parentbased_traceidratio@0.4"
    )
    assert type(for_parent_trace_id["my.module"]) is ParentBasedTraceIdRatio
    assert for_parent_trace_id["my.module"]._root.rate == 0.4
