import base64

from openinference.instrumentation.agno import AgnoInstrumentor
from opentelemetry import trace as trace_api
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Set environment variables for Langfuse


class LangfuseSettings(BaseSettings):
    public_key: str = Field(..., description="Langfuse public key")
    secret_key: str = Field(..., description="Langfuse secret key")
    base_url: str = Field(..., description="Langfuse base url")

    model_config = SettingsConfigDict(env_prefix="LANGFUSE_")


langfuse_settings = LangfuseSettings()


def create_span_exporter():
    langfuse_auth = base64.b64encode(
        f"{langfuse_settings.public_key}:{langfuse_settings.secret_key}".encode()
    ).decode()
    span_exporter = OTLPSpanExporter(
        endpoint=f"{langfuse_settings.base_url}/api/public/otel/v1/traces",
        headers={"Authorization": f"Basic {langfuse_auth}"},
    )

    return span_exporter


# Configure the tracer provider
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(SimpleSpanProcessor(create_span_exporter()))
trace_api.set_tracer_provider(tracer_provider=tracer_provider)

# Start instrumenting agno
AgnoInstrumentor().instrument()
