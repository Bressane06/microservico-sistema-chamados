
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Prioridade(str, Enum):
    BAIXA = "BAIXA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"


class StatusChamado(str, Enum):
    ABERTO = "ABERTO"
    EM_ATENDIMENTO = "EM_ATENDIMENTO"
    PENDENTE = "PENDENTE"
    RESOLVIDO = "RESOLVIDO"
    CANCELADO = "CANCELADO"


class ChamadoCriacao(BaseModel):
    titulo: str = Field(min_length=3, max_length=150)
    descricao: str = Field(min_length=5)
    categoria: str = Field(min_length=2, max_length=80)
    prioridade: Prioridade = Prioridade.MEDIA


class ChamadoAtualizacao(BaseModel):
    descricao: Optional[str] = Field(default=None, min_length=5)
    prioridade: Optional[Prioridade] = None
    status: Optional[StatusChamado] = None


class HistoricoResposta(BaseModel):
    id: int
    chamado_id: int
    campo: str
    valor_anterior: Optional[str]
    valor_novo: Optional[str]
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class ChamadoResposta(BaseModel):
    id: int
    titulo: str
    descricao: str
    categoria: str
    prioridade: Prioridade
    status: StatusChamado
    tecnico_id: Optional[int]
    criado_em: datetime
    atualizado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class AtribuicaoSolicitacao(BaseModel):
    tecnico_id: int = Field(gt=0)
