
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


def agora_utc():
    """Retorna a data e hora atuais em UTC, sem fuso no valor armazenado."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Chamado(Base):
    __tablename__ = "chamados"

    id = Column(Integer, primary_key=True, index=True)

    titulo = Column(String(150), nullable=False)
    descricao = Column(Text, nullable=False)
    categoria = Column(String(80), nullable=False)
    prioridade = Column(String(20), nullable=False, default="MEDIA")
    status = Column(String(20), nullable=False, default="ABERTO")

    # Referência lógica ao técnico mantido pelo serviço Java.
    # Não é uma chave estrangeira para o banco de técnicos.
    tecnico_id = Column(Integer, nullable=True)

    criado_em = Column(DateTime, nullable=False, default=agora_utc)
    atualizado_em = Column(
        DateTime,
        nullable=False,
        default=agora_utc,
        onupdate=agora_utc,
    )

    historicos = relationship(
        "HistoricoChamado",
        back_populates="chamado",
        cascade="all, delete-orphan",
        order_by="HistoricoChamado.criado_em",
    )


class HistoricoChamado(Base):
    __tablename__ = "historico_chamados"

    id = Column(Integer, primary_key=True, index=True)

    chamado_id = Column(
        Integer,
        ForeignKey("chamados.id"),
        nullable=False,
        index=True,
    )

    campo = Column(String(50), nullable=False)
    valor_anterior = Column(Text, nullable=True)
    valor_novo = Column(Text, nullable=True)
    criado_em = Column(DateTime, nullable=False, default=agora_utc)

    chamado = relationship(
        "Chamado",
        back_populates="historicos",
    )
