import os

import httpx
from fastapi import HTTPException, status


TECNICOS_API_URL = os.getenv(
    "TECNICOS_API_URL",
    "http://localhost:8081",
)


def consultar_tecnico(tecnico_id: int) -> dict:
    """Consulta um técnico no microsserviço Java."""

    url = f"{TECNICOS_API_URL}/tecnicos/{tecnico_id}"

    try:
        resposta = httpx.get(url, timeout=5.0)

        if resposta.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Técnico não encontrado ou inativo.",
            )

        resposta.raise_for_status()

        return resposta.json()

    except HTTPException:
        raise

    except httpx.HTTPStatusError as erro:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="O serviço de técnicos retornou um erro.",
        ) from erro

    except httpx.RequestError as erro:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível conectar ao serviço de técnicos.",
        ) from erro