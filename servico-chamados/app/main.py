
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from app.database import Base, engine
from app import models
from app.routes.chamados import router as chamados_router


# Configuração do OpenTelemetry.
resource = Resource.create({
    "service.name": "servico-chamados"
})

provider = TracerProvider(resource=resource)

exporter = OTLPSpanExporter(
    endpoint="http://jaeger:4317",
    insecure=True
)

provider.add_span_processor(
    BatchSpanProcessor(exporter)
)

trace.set_tracer_provider(provider)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria as tabelas que ainda não existem.
    Base.metadata.create_all(bind=engine)

    yield

    # Finaliza o envio dos traces pendentes.
    provider.force_flush()
    provider.shutdown()


app = FastAPI(
    title="API de Chamados",
    description=(
        "Microsserviço de gerenciamento de chamados "
        "de suporte técnico."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(chamados_router)

# Instrumenta as requisições recebidas pelo FastAPI.
FastAPIInstrumentor.instrument_app(app)

# Instrumenta as requisições HTTP realizadas pelo HTTPX.
HTTPXClientInstrumentor().instrument()


@app.get("/", tags=["Inicialização"])
def inicio():
    return {
        "servico": "API de Chamados",
        "status": "online",
        "documentacao": "/docs",
    }


@app.get("/health", tags=["Monitoramento"])
def health():
    return {"status": "ok"}


# Disponibiliza métricas para o Prometheus.
Instrumentator().instrument(app).expose(app)
