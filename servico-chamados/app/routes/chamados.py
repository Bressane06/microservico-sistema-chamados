
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.services.tecnicos_client import consultar_tecnico
from app.database import get_db
from app.models import Chamado, HistoricoChamado
from app.schemas import (
    AtribuicaoSolicitacao,
    ChamadoAtualizacao,
    ChamadoCriacao,
    ChamadoResposta,
    HistoricoResposta,
    StatusChamado,
)
from app.services.eventos import (
    publicar_chamado_atribuido,
    publicar_chamado_encerrado,
)
from app.services.historico import registrar_alteracao

router = APIRouter(prefix="/chamados", tags=["Chamados"])


def buscar_chamado(db: Session, chamado_id: int) -> Chamado:
    chamado = db.get(Chamado, chamado_id)

    if chamado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chamado não encontrado.",
        )

    return chamado


@router.post(
    "",
    response_model=ChamadoResposta,
    status_code=status.HTTP_201_CREATED,
)
def criar_chamado(
    dados: ChamadoCriacao,
    db: Session = Depends(get_db),
):
    chamado = Chamado(
        titulo=dados.titulo,
        descricao=dados.descricao,
        categoria=dados.categoria,
        prioridade=dados.prioridade.value,
        status=StatusChamado.ABERTO.value,
    )

    try:
        db.add(chamado)
        db.flush()

        registrar_alteracao(
            db,
            chamado,
            "criacao",
            None,
            "Chamado criado",
        )

        db.commit()
        db.refresh(chamado)

        return chamado

    except Exception:
        db.rollback()
        raise


@router.get("", response_model=list[ChamadoResposta])
def listar_chamados(
    status_chamado: StatusChamado | None = Query(
        default=None,
        alias="status",
    ),
    categoria: str | None = None,
    db: Session = Depends(get_db),
):
    consulta = db.query(Chamado)

    if status_chamado is not None:
        consulta = consulta.filter(
            Chamado.status == status_chamado.value
        )

    if categoria is not None:
        consulta = consulta.filter(Chamado.categoria == categoria)

    return consulta.order_by(Chamado.criado_em.desc()).all()


@router.get("/{chamado_id}", response_model=ChamadoResposta)
def consultar_chamado(
    chamado_id: int,
    db: Session = Depends(get_db),
):
    return buscar_chamado(db, chamado_id)


@router.patch("/{chamado_id}", response_model=ChamadoResposta)
def atualizar_chamado(
    chamado_id: int,
    dados: ChamadoAtualizacao,
    db: Session = Depends(get_db),
):
    chamado = buscar_chamado(db, chamado_id)

    if chamado.status in (
        StatusChamado.CANCELADO.value,
        StatusChamado.RESOLVIDO.value,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível atualizar um chamado encerrado.",
        )

    alteracoes = dados.model_dump(exclude_unset=True)

    if not alteracoes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe pelo menos um campo para atualizar.",
        )

    for campo, valor in alteracoes.items():
        valor_novo = valor.value if hasattr(valor, "value") else valor
        valor_anterior = getattr(chamado, campo)

        if valor_anterior == valor_novo:
            continue

        if (
            campo == "status"
            and valor_novo == StatusChamado.ABERTO.value
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Não é permitido reabrir chamados por esta rota.",
            )

        registrar_alteracao(
            db,
            chamado,
            campo,
            valor_anterior,
            valor_novo,
        )

        setattr(chamado, campo, valor_novo)

    try:
        db.commit()
        db.refresh(chamado)

        # Evento publicado somente após o commit.
        if chamado.status in (
            StatusChamado.CANCELADO.value,
            StatusChamado.RESOLVIDO.value,
        ):
            publicar_chamado_encerrado(chamado)

        return chamado

    except Exception:
        db.rollback()
        raise


@router.post(
    "/{chamado_id}/cancelar",
    response_model=ChamadoResposta,
)
def cancelar_chamado(
    chamado_id: int,
    db: Session = Depends(get_db),
):
    chamado = buscar_chamado(db, chamado_id)

    if chamado.status in (
        StatusChamado.CANCELADO.value,
        StatusChamado.RESOLVIDO.value,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O chamado já está encerrado.",
        )

    registrar_alteracao(
        db,
        chamado,
        "status",
        chamado.status,
        StatusChamado.CANCELADO.value,
    )

    chamado.status = StatusChamado.CANCELADO.value

    try:
        db.commit()
        db.refresh(chamado)

        publicar_chamado_encerrado(chamado)

        return chamado

    except Exception:
        db.rollback()
        raise


@router.get(
    "/{chamado_id}/historico",
    response_model=list[HistoricoResposta],
)
def consultar_historico(
    chamado_id: int,
    db: Session = Depends(get_db),
):
    buscar_chamado(db, chamado_id)

    return (
        db.query(HistoricoChamado)
        .filter(HistoricoChamado.chamado_id == chamado_id)
        .order_by(HistoricoChamado.criado_em.asc())
        .all()
    )


@router.post(
    "/{chamado_id}/atribuir-tecnico",
    response_model=ChamadoResposta,
)
def atribuir_tecnico(
    chamado_id: int,
    dados: AtribuicaoSolicitacao,
    db: Session = Depends(get_db),
):
    chamado = buscar_chamado(db, chamado_id)

    # Não permite atribuir técnicos a chamados encerrados.
    if chamado.status in (
        StatusChamado.CANCELADO.value,
        StatusChamado.RESOLVIDO.value,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não é possível atribuir técnico a um chamado encerrado.",
        )

    # Verifica se já está atribuído ao mesmo técnico.
    if chamado.tecnico_id == dados.tecnico_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esse técnico já está atribuído ao chamado.",
        )

    # Consulta o técnico no microsserviço Java.
    tecnico = consultar_tecnico(dados.tecnico_id)

    # Verifica se o técnico está ativo e disponível.
    if not tecnico.get("ativo") or not tecnico.get("disponivel"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O técnico não está disponível para receber chamados.",
        )

    tecnico_anterior_id = chamado.tecnico_id

    valor_anterior = (
        str(chamado.tecnico_id)
        if chamado.tecnico_id is not None
        else None
    )

    try:
        chamado.tecnico_id = dados.tecnico_id

        registrar_alteracao(
            db,
            chamado,
            "tecnico_id",
            valor_anterior,
            str(dados.tecnico_id),
        )

        db.commit()
        db.refresh(chamado)

        # Notifica o serviço de técnicos (assíncrono, via RabbitMQ).
        publicar_chamado_atribuido(chamado, tecnico_anterior_id)

        return chamado

    except Exception:
        db.rollback()
        raise
