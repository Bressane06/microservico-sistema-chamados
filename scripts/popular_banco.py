#!/usr/bin/env python3
"""Popula o sistema com dados de exemplo usando as APIs (via API Gateway).

Os dados são gravados pelas APIs, e não direto nos bancos, para respeitar o
princípio de "database per service", passar pelas validações de cada serviço
e disparar os eventos do RabbitMQ (disponibilidade dos técnicos).

Usa apenas a biblioteca padrão do Python 3.9+ (nenhuma instalação necessária).

Exemplos:
    python scripts/popular_banco.py
    python scripts/popular_banco.py --url http://localhost:8080
    python scripts/popular_banco.py --forcar     # cria os chamados mesmo se já existirem
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

TECNICOS = [
    {"nome": "Ana Souza", "email": "ana.souza@suporte.com", "especialidade": "Redes"},
    {"nome": "Bruno Lima", "email": "bruno.lima@suporte.com", "especialidade": "Infraestrutura"},
    {"nome": "Carla Mendes", "email": "carla.mendes@suporte.com", "especialidade": "Banco de Dados"},
    {"nome": "Diego Alves", "email": "diego.alves@suporte.com", "especialidade": "Segurança"},
    {"nome": "Elisa Ferreira", "email": "elisa.ferreira@suporte.com", "especialidade": "Sistemas"},
    {"nome": "Felipe Rocha", "email": "felipe.rocha@suporte.com", "especialidade": "Hardware"},
]

CHAMADOS = [
    ("Sem acesso à VPN", "Erro de autenticação ao conectar na VPN corporativa.", "Redes", "ALTA"),
    ("Servidor de arquivos lento", "Compartilhamentos demoram mais de 1 minuto para abrir.", "Infraestrutura", "MEDIA"),
    ("Consulta travando no banco", "Relatório mensal excede o tempo limite no PostgreSQL.", "Banco de Dados", "CRITICA"),
    ("E-mail suspeito recebido", "Mensagem de phishing recebida por vários usuários.", "Segurança", "ALTA"),
    ("Sistema financeiro fora do ar", "Erro 500 ao acessar o módulo de contas a pagar.", "Sistemas", "CRITICA"),
    ("Monitor sem imagem", "Monitor da recepção não liga após queda de energia.", "Hardware", "BAIXA"),
    ("Wi-Fi instável no 2º andar", "Quedas frequentes de sinal na sala de reuniões.", "Redes", "MEDIA"),
    ("Solicitação de novo usuário", "Criar acesso para colaborador do setor comercial.", "Sistemas", "BAIXA"),
    ("Backup não concluído", "Rotina de backup noturno terminou com erro.", "Infraestrutura", "ALTA"),
    ("Impressora fora da rede", "Impressora do RH não aparece para os computadores.", "Hardware", "BAIXA"),
    ("Senha expirada em massa", "Vários usuários bloqueados após política de expiração.", "Segurança", "MEDIA"),
    ("Lentidão no ERP", "Telas do ERP demoram para carregar no horário de pico.", "Sistemas", "MEDIA"),
]


class ErroApi(Exception):
    def __init__(self, status, detalhe):
        super().__init__(f"HTTP {status}: {detalhe}")
        self.status = status
        self.detalhe = detalhe


def requisicao(metodo, url, corpo=None, timeout=15):
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request(
        url,
        data=dados,
        method=metodo,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            texto = resp.read().decode("utf-8")
            return json.loads(texto) if texto else None
    except urllib.error.HTTPError as erro:
        texto = erro.read().decode("utf-8", errors="replace")
        try:
            detalhe = json.loads(texto).get("detail") or json.loads(texto).get("message") or texto
        except (ValueError, AttributeError):
            detalhe = texto
        raise ErroApi(erro.code, detalhe) from None


def aguardar_gateway(base, tentativas=30):
    print(f"Aguardando o gateway em {base} ...")
    for _ in range(tentativas):
        try:
            requisicao("GET", f"{base}/health", timeout=3)
            return
        except Exception:
            time.sleep(2)
    sys.exit("Gateway indisponível. Rode 'docker compose up -d' e confira 'docker compose ps'.")


def popular_tecnicos(url_tecnicos):
    print("\n== Técnicos (serviço Java) ==")
    existentes = {t["email"]: t for t in requisicao("GET", f"{url_tecnicos}/tecnicos")}
    ids = []

    for dados in TECNICOS:
        if dados["email"] in existentes:
            tecnico = existentes[dados["email"]]
            print(f"  = já existe: {dados['nome']} (id {tecnico['id']})")
        else:
            tecnico = requisicao("POST", f"{url_tecnicos}/tecnicos", dados)
            print(f"  + criado:    {dados['nome']} (id {tecnico['id']})")
        ids.append(tecnico["id"])

    return ids


def popular_chamados(url_chamados, tecnicos, forcar):
    print("\n== Chamados (serviço Python) ==")
    titulos_existentes = {c["titulo"] for c in requisicao("GET", f"{url_chamados}/chamados")}

    if not forcar and any(c[0] in titulos_existentes for c in CHAMADOS):
        print("  Chamados de exemplo já existem. Use --forcar para criá-los novamente.")
        return None

    criados = []
    for titulo, descricao, categoria, prioridade in CHAMADOS:
        chamado = requisicao(
            "POST",
            f"{url_chamados}/chamados",
            {"titulo": titulo, "descricao": descricao, "categoria": categoria, "prioridade": prioridade},
        )
        criados.append(chamado["id"])
        print(f"  + chamado {chamado['id']:>3} [{prioridade:<7}] {titulo}")

    simular_atendimento(url_chamados, criados, tecnicos)
    return criados


def simular_atendimento(url, chamados, tecnicos):
    """Gera um histórico variado: atribuições, andamento, resolução e cancelamento.

    Cada técnico atende no máximo um chamado, porque a disponibilidade é
    atualizada de forma assíncrona pelo RabbitMQ.
    """
    print("\n== Simulando atendimento ==")

    def chamado_n(i):
        return f"{url}/chamados/{chamados[i]}"

    # 4 chamados atribuídos a técnicos distintos (os técnicos ficam indisponíveis)
    for i in range(4):
        requisicao("POST", f"{chamado_n(i)}/atribuir-tecnico", {"tecnico_id": tecnicos[i]})
        print(f"  chamado {chamados[i]} atribuído ao técnico {tecnicos[i]}")

    # dois deles entram em atendimento
    for i in (0, 2):
        requisicao("PATCH", chamado_n(i), {"status": "EM_ATENDIMENTO"})
        print(f"  chamado {chamados[i]} -> EM_ATENDIMENTO")

    # um fica pendente e tem a prioridade revista (gera histórico)
    requisicao("PATCH", chamado_n(3), {"status": "PENDENTE", "prioridade": "CRITICA"})
    print(f"  chamado {chamados[3]} -> PENDENTE (prioridade CRITICA)")

    # um chamado atribuído e resolvido (o técnico é liberado pelo evento)
    requisicao("POST", f"{chamado_n(4)}/atribuir-tecnico", {"tecnico_id": tecnicos[4]})
    requisicao("PATCH", chamado_n(4), {"status": "RESOLVIDO"})
    print(f"  chamado {chamados[4]} atribuído e RESOLVIDO (técnico {tecnicos[4]} liberado)")

    # um chamado cancelado
    requisicao("POST", f"{chamado_n(5)}/cancelar")
    print(f"  chamado {chamados[5]} CANCELADO")

    # ajuste de prioridade em um chamado aberto
    requisicao("PATCH", chamado_n(6), {"prioridade": "ALTA"})
    print(f"  chamado {chamados[6]} prioridade -> ALTA")


def resumo(url_chamados, url_tecnicos):
    print("\n== Resumo ==")
    por_status = {}
    for c in requisicao("GET", f"{url_chamados}/chamados"):
        por_status[c["status"]] = por_status.get(c["status"], 0) + 1
    for status, qtd in sorted(por_status.items()):
        print(f"  chamados {status:<15} {qtd}")

    print("\n  Técnicos (a disponibilidade é atualizada via RabbitMQ):")
    for t in requisicao("GET", f"{url_tecnicos}/tecnicos"):
        estado = "disponível" if t["disponivel"] else "ocupado"
        print(f"   - {t['id']:>3} {t['nome']:<16} {t['especialidade']:<15} {estado}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://localhost:8080", help="URL do API Gateway (padrão: %(default)s)")
    ap.add_argument("--chamados-url", help="URL direta do serviço de chamados (ignora o gateway)")
    ap.add_argument("--tecnicos-url", help="URL direta do serviço de técnicos (ignora o gateway)")
    ap.add_argument("--forcar", action="store_true", help="cria os chamados mesmo que já existam")
    args = ap.parse_args()

    base = args.url.rstrip("/")
    url_chamados = (args.chamados_url or base).rstrip("/")
    url_tecnicos = (args.tecnicos_url or base).rstrip("/")

    if not (args.chamados_url and args.tecnicos_url):
        aguardar_gateway(base)

    try:
        tecnicos = popular_tecnicos(url_tecnicos)
        popular_chamados(url_chamados, tecnicos, args.forcar)
        time.sleep(2)  # tempo para o consumidor do RabbitMQ atualizar os técnicos
        resumo(url_chamados, url_tecnicos)
    except ErroApi as erro:
        sys.exit(f"\nErro da API: {erro}")
    except urllib.error.URLError as erro:
        sys.exit(f"\nNão foi possível conectar: {erro.reason}")

    print("\nConcluído.")


if __name__ == "__main__":
    main()
