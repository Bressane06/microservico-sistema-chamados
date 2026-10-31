
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.database import Base, engine
from app import models
from app.routes.chamados import router as chamados_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria as tabelas que ainda não existem.
    Base.metadata.create_all(bind=engine)

    yield

    # O SQLAlchemy gerencia o fechamento das sessões
    # individualmente em cada requisição.


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
