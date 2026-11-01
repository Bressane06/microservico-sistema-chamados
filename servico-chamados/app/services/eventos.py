"""Publicação de eventos de domínio no RabbitMQ.

Os eventos são publicados DEPOIS do commit no banco. Se o broker estiver
indisponível, a falha é registrada em log e a requisição HTTP continua
funcionando (o chamado já foi gravado). Essa limitação (dual write) poderia
ser eliminada com o padrão Transactional Outbox.
"""

import json
import logging
import os
from datetime import datetime, timezone

import pika

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL",
    "amqp://guest:guest@localhost:5672/%2F",
)

EXCHANGE = "chamados.eventos"
ROTA_ATRIBUIDO = "chamado.atribuido"
ROTA_ENCERRADO = "chamado.encerrado"


def publicar_evento(
    routing_key: str,
    payload: dict,
    headers: dict | None = None,
) -> bool:
    """Publica um evento JSON no exchange de chamados.

    Retorna True se publicou, False se houve falha (nunca lança exceção).
    """
    corpo = {
        **payload,
        "evento": routing_key,
        "ocorrido_em": datetime.now(timezone.utc).isoformat(),
    }

    try:
        parametros = pika.URLParameters(RABBITMQ_URL)
        parametros.socket_timeout = 3
        parametros.blocked_connection_timeout = 3
        parametros.connection_attempts = 2
        parametros.retry_delay = 1

        with pika.BlockingConnection(parametros) as conexao:
            canal = conexao.channel()
            canal.exchange_declare(
                exchange=EXCHANGE,
                exchange_type="topic",
                durable=True,
            )
            canal.basic_publish(
                exchange=EXCHANGE,
                routing_key=routing_key,
                body=json.dumps(corpo).encode("utf-8"),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,  # mensagem persistente
                    headers=headers or {},
                ),
            )

        logger.info("Evento publicado: %s %s", routing_key, payload)
        return True

    except Exception:
        logger.exception(
            "Falha ao publicar o evento %s no RabbitMQ.", routing_key
        )
        return False


def publicar_chamado_atribuido(chamado, tecnico_anterior_id: int | None):
    """Informa que um técnico foi atribuído (e qual foi substituído)."""
    # Os identificadores também vão nos cabeçalhos AMQP para o consumidor
    headers = {
        "chamado_id": chamado.id,
        "tecnico_id": chamado.tecnico_id,
    }
    if tecnico_anterior_id is not None:
        headers["tecnico_anterior_id"] = tecnico_anterior_id

    return publicar_evento(
        ROTA_ATRIBUIDO,
        {
            "chamado_id": chamado.id,
            "tecnico_id": chamado.tecnico_id,
            "tecnico_anterior_id": tecnico_anterior_id,
        },
        headers,
    )


def publicar_chamado_encerrado(chamado):
    """Informa que o chamado foi resolvido/cancelado (libera o técnico)."""
    if chamado.tecnico_id is None:
        return False

    return publicar_evento(
        ROTA_ENCERRADO,
        {
            "chamado_id": chamado.id,
            "tecnico_id": chamado.tecnico_id,
            "status": chamado.status,
        },
        {
            "chamado_id": chamado.id,
            "tecnico_id": chamado.tecnico_id,
        },
    )
