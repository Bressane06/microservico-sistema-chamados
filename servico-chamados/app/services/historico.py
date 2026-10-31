
from sqlalchemy.orm import Session

from app.models import Chamado, HistoricoChamado


def registrar_alteracao(
    db: Session,
    chamado: Chamado,
    campo: str,
    valor_anterior,
    valor_novo,
):
    """Adiciona uma alteração ao histórico da transação atual."""

    historico = HistoricoChamado(
        chamado_id=chamado.id,
        campo=campo,
        valor_anterior=(
            str(valor_anterior) if valor_anterior is not None else None
        ),
        valor_novo=(
            str(valor_novo) if valor_novo is not None else None
        ),
    )

    db.add(historico)
