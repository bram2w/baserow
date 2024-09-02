from typing import Optional

from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.sdk.trace import Span
from opentelemetry.sdk.trace.sampling import _KNOWN_SAMPLERS as ROOT_KNOWN_SAMPLERS
from opentelemetry.sdk.trace.sampling import (
    Decision,
    SamplingResult,
    TraceIdRatioBased,
    _get_parent_trace_state,
)


class ForcableTraceIdRatioBased(TraceIdRatioBased):
    def should_sample(
        self,
        parent_context: Optional["Context"],
        trace_id: int,
        name: str,
        kind=None,
        attributes=None,
        links=None,
        trace_state=None,
    ) -> SamplingResult:
        current_span = trace.get_current_span(parent_context)

        if isinstance(current_span, Span):
            span_attributes = current_span.attributes
            # Check if the HTTP request contains the query parameter to force full
            # tracing, and if so do the full trace.
            http_url = span_attributes.get("http.url", "")
            if "force_full_otel_trace=true" in http_url:
                return SamplingResult(
                    Decision.RECORD_AND_SAMPLE,
                    span_attributes,
                    _get_parent_trace_state(parent_context),
                )
        # If the full trace query parameter is not provided, then fallback on the
        # original TraceIdRatioBased class.
        return super().should_sample(
            parent_context, trace_id, name, kind, attributes, links, trace_state
        )


ROOT_KNOWN_SAMPLERS["traceidratio"] = ForcableTraceIdRatioBased
