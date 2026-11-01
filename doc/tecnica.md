# Documentação técnica — Sistema de Chamados

Este documento descreve a arquitetura, os componentes, os contratos das APIs, a persistência, a comunicação distribuída e a observabilidade do Sistema de Chamados.

Para instalação e execução do ambiente, consulte o [guia principal](../README.md).

## 1. Visão geral

O sistema é uma aplicação distribuída para gerenciamento de chamados de suporte técnico, organizada em dois microsserviços independentes:

| Microsserviço | Linguagem e framework | Responsabilidade |
|---|---|---|
| Serviço de chamados | Python 3.12, FastAPI e SQLAlchemy | Cadastro, consulta, atualização, cancelamento, exclusão e histórico de chamados |
| Serviço de técnicos | Java 21, Spring Boot, Spring Data JPA e Hibernate | Cadastro, consulta, atualização e desativação de técnicos; disponibilidade |

Cada microsserviço é responsável pelo próprio banco PostgreSQL (*database per service*). O NGINX funciona como API Gateway e ponto único de entrada para os clientes.

Além da comunicação HTTP síncrona, os serviços utilizam RabbitMQ para propagar eventos de domínio e atualizar a disponibilidade dos técnicos de forma assíncrona.

## 2. Arquitetura e infraestrutura

### 2.1. Componentes

| Componente | Imagem/tecnologia | Função |
|---|---|---|
| `api-gateway` | NGINX 1.27 Alpine | Roteamento das requisições e entrada única |
| `api-chamados` | Python 3.12 + FastAPI | API de chamados |
| `db-chamados` | PostgreSQL 17 | Dados de chamados e histórico |
| `api-tecnicos` | Eclipse Temurin 21 + Spring Boot | API de técnicos |
| `db-tecnicos` | PostgreSQL 17 | Dados dos técnicos |
| `rabbitmq` | RabbitMQ 3.13 Management | Exchange, filas e eventos assíncronos |
| `jaeger` | Jaeger 2.22 | Coleta e visualização de traces |
| `prometheus` | Prometheus 3.5 | Coleta de métricas |
| `grafana` | Grafana 12.1 | Dashboards de métricas |

### 2.2. Fluxo de requisições

```text
                         Cliente
                            |
                     HTTP / REST
                            |
                    API Gateway (NGINX)
                       :8080 (host)
                      /           \
                     /             \
             API Chamados       API Técnicos
             FastAPI :8000      Spring :8081
                  |                  |
             PostgreSQL          PostgreSQL
             db-chamados          db-tecnicos
                  |
            HTTP para validar técnico
                  |
             API Técnicos

       API Chamados -- evento --> RabbitMQ
                                      |
                                API Técnicos
                         atualiza disponibilidade

       APIs -- traces --> Jaeger
       APIs/RabbitMQ -- métricas --> Prometheus --> Grafana
```

### 2.3. Princípios adotados

- **Database per service:** cada serviço acessa exclusivamente seu próprio banco.
- **API Gateway:** clientes acessam as APIs pelo NGINX, sem depender da topologia interna.
- **Comunicação síncrona:** a API de chamados consulta a API de técnicos para validar a atribuição.
- **Comunicação assíncrona:** eventos RabbitMQ atualizam a disponibilidade dos técnicos.
- **Rastreamento distribuído:** OpenTelemetry propaga traces entre componentes instrumentados.
- **Persistência:** volumes Docker mantêm os dados entre reinicializações dos containers.

### 2.4. Redes Docker

- `rede-chamados`: API de chamados e banco de chamados.
- `rede-tecnicos`: API de técnicos e banco de técnicos.
- `rede-servicos`: gateway, microsserviços, RabbitMQ e ferramentas de observabilidade.

Os bancos não compartilham uma rede entre si. Os serviços de aplicação participam da rede do próprio banco e da rede compartilhada de serviços.

## 3. Estrutura do repositório

```text
.
├── README.md
├── doc/
│   └── tecnica.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── gateway/
│   └── nginx.conf
├── observabilidade/
│   ├── prometheus.yml
│   └── grafana/
│       ├── dashboards/
│       │   └── sistema-chamados.json
│       └── provisioning/
│           ├── dashboards/
│           │   └── dashboards.yml
│           └── datasources/
│               └── prometheus.yml
├── scripts/
│   └── popular_banco.py
├── servico-chamados/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── routes/
│   │   │   └── chamados.py
│   │   └── services/
│   │       ├── eventos.py
│   │       ├── historico.py
│   │       └── tecnicos_client.py
│   ├── requirements.txt
│   └── Dockerfile
└── servico-tecnicos/
    ├── src/
    │   ├── main/java/br/com/suporte/servico_tecnicos/
    │   │   ├── controller/
    │   │   ├── dto/
    │   │   ├── entity/
    │   │   ├── messaging/
    │   │   ├── repository/
    │   │   ├── service/
    │   │   └── ServicoTecnicosApplication.java
    │   └── main/resources/
    │       └── application.properties
    ├── pom.xml
    ├── mvnw
    └── Dockerfile
```

## 4. Modelo de dados

### 4.1. Banco de chamados

Tabela `chamados`:

| Campo | Descrição |
|---|---|
| `id` | Identificador do chamado |
| `titulo` | Título resumido (até 150 caracteres) |
| `descricao` | Descrição do problema |
| `categoria` | Categoria do atendimento |
| `prioridade` | `BAIXA`, `MEDIA`, `ALTA` ou `CRITICA` |
| `status` | Estado atual do chamado |
| `tecnico_id` | Referência lógica ao técnico do serviço Java |
| `criado_em` | Data/hora de criação em UTC |
| `atualizado_em` | Data/hora da última atualização |

Tabela `historico_chamados`:

| Campo | Descrição |
|---|---|
| `id` | Identificador do registro |
| `chamado_id` | Chave estrangeira para `chamados.id` |
| `campo` | Campo que sofreu alteração |
| `valor_anterior` | Valor anterior, quando existente |
| `valor_novo` | Novo valor |
| `criado_em` | Data/hora da alteração |

O relacionamento entre chamado e histórico utiliza `cascade="all, delete-orphan"`. Portanto, quando um chamado elegível é excluído, seu histórico também é removido.

### 4.2. Banco de técnicos

A entidade `Tecnico` contém:

| Campo | Descrição |
|---|---|
| `id` | Identificador do técnico |
| `nome` | Nome |
| `email` | E-mail |
| `especialidade` | Área de atuação |
| `disponivel` | Indica se pode receber um chamado |
| `ativo` | Indica se o cadastro está ativo |
| `criadoEm` | Data de criação |

Não há chave estrangeira entre os bancos. `tecnico_id` é uma referência lógica validada pela API Java.

## 5. Microsserviço de chamados — Python

**Tecnologias:** Python 3.12, FastAPI, SQLAlchemy, Pydantic, psycopg, HTTPX, Pika, OpenTelemetry e prometheus-fastapi-instrumentator.

A aplicação cria as tabelas mapeadas pelo SQLAlchemy durante o ciclo de inicialização, caso ainda não existam.

### 5.1. Endpoints

Todos os endpoints abaixo são acessados pelo gateway em `http://localhost:8080`.

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/chamados` | Cria um chamado |
| `GET` | `/chamados` | Lista chamados; aceita filtros `status` e `categoria` |
| `GET` | `/chamados/{id}` | Consulta um chamado |
| `PATCH` | `/chamados/{id}` | Atualiza descrição, prioridade ou status |
| `POST` | `/chamados/{id}/cancelar` | Cancela um chamado |
| `GET` | `/chamados/{id}/historico` | Consulta o histórico |
| `POST` | `/chamados/{id}/atribuir-tecnico` | Valida e atribui um técnico |
| `DELETE` | `/chamados/{id}` | Exclui chamado e histórico, quando permitido |

### 5.2. Regras de negócio

- O cadastro exige título, descrição e categoria válidos; a prioridade padrão é `MEDIA`.
- O status inicial é `ABERTO`.
- A listagem permite filtrar por status e categoria.
- Chamados `RESOLVIDO` ou `CANCELADO` não podem ser atualizados nem receber atribuição.
- A rota de atualização não permite reabrir um chamado para `ABERTO`.
- O cancelamento mantém o registro para consulta.
- Chamados resolvidos não podem ser excluídos, preservando a auditoria.
- A exclusão de um chamado permitido remove também seu histórico.
- A atribuição consulta o técnico no serviço Java e exige que esteja ativo e disponível.
- As alterações relevantes são registradas em `historico_chamados`.

### 5.3. Exemplo de criação

```http
POST /chamados
Content-Type: application/json
```

```json
{
  "titulo": "Sem acesso à VPN",
  "descricao": "Erro de autenticação ao conectar na VPN corporativa.",
  "categoria": "Redes",
  "prioridade": "ALTA"
}
```

### 5.4. Exemplo de atribuição

```http
POST /chamados/1/atribuir-tecnico
Content-Type: application/json
```

```json
{
  "tecnico_id": 1
}
```

## 6. Microsserviço de técnicos — Java

**Tecnologias:** Java 21, Spring Boot, Spring Web MVC, Spring Data JPA, Hibernate, PostgreSQL, Spring AMQP, Actuator, Micrometer Prometheus e springdoc OpenAPI.

O serviço utiliza camadas de controller, service, repository, entity e DTO.

### 6.1. Endpoints

Todos os endpoints são acessados pelo gateway em `http://localhost:8080`.

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/tecnicos` | Cadastra técnico |
| `GET` | `/tecnicos` | Lista técnicos |
| `GET` | `/tecnicos/{id}` | Consulta técnico |
| `PUT` | `/tecnicos/{id}` | Atualiza dados do técnico |
| `DELETE` | `/tecnicos/{id}` | Desativa técnico |
| `GET` | `/tecnicos/disponiveis` | Lista técnicos disponíveis |

A operação `DELETE` realiza desativação lógica, conforme a regra implementada no serviço, em vez de apagar definitivamente o cadastro.

### 6.2. Documentação da API

A documentação OpenAPI do Spring é disponibilizada pelo gateway em:

- Swagger UI: `http://localhost:8080/swagger-ui/index.html`
- OpenAPI JSON: `http://localhost:8080/v3/api-docs`

## 7. API Gateway — NGINX

O gateway publica a porta `8080` no host e encaminha as requisições para os serviços na rede Docker.

| Caminho | Destino |
|---|---|
| `/chamados/**` | `api-chamados:8000` |
| `/docs` e `/openapi.json` | FastAPI |
| `/tecnicos/**` | `api-tecnicos:8081` |
| `/swagger-ui/**` e `/v3/api-docs/**` | Spring Boot |
| `/health` | Healthcheck do próprio gateway |

O gateway encaminha cabeçalhos de proxy, `traceparent` e `X-Request-ID`. Respostas de indisponibilidade dos serviços upstream são convertidas em HTTP 503 com corpo JSON. Rotas não mapeadas retornam HTTP 404.

As portas internas `8000` e `8081` são expostas apenas para a rede Docker, não diretamente no host.

## 8. Comunicação entre microsserviços

### 8.1. HTTP síncrono — validação da atribuição

1. O cliente solicita a atribuição na API de chamados.
2. A API Python chama o serviço Java por HTTP usando `tecnicos_client.py`.
3. A API Java consulta seu próprio PostgreSQL e retorna os dados do técnico.
4. A API Python valida existência, atividade e disponibilidade.
5. Se a validação passar, o chamado recebe o `tecnico_id` e a alteração é registrada no histórico.
6. Após o commit, a API Python publica o evento de atribuição no RabbitMQ.

Tratamento de falhas previsto no cliente HTTP: técnico não encontrado (404), técnico indisponível/inativo (409), resposta inválida ou erro upstream (502) e serviço inacessível (503). O timeout evita espera indefinida.

### 8.2. RabbitMQ — eventos assíncronos

O serviço Python publica mensagens JSON em um exchange durável do tipo `topic`:

- Exchange: `chamados.eventos`
- Routing key `chamado.atribuido`
- Routing key `chamado.encerrado`

| Evento | Produtor | Consumidor | Efeito esperado |
|---|---|---|---|
| `chamado.atribuido` | Serviço Python | Serviço Java | Marca o novo técnico como indisponível e libera o técnico anterior, se houver |
| `chamado.encerrado` | Serviço Python | Serviço Java | Libera o técnico associado ao chamado encerrado ou excluído |

O consumidor Java é configurado por Spring AMQP. A disponibilidade é atualizada de forma assíncrona, portanto existe consistência eventual: pode haver um pequeno intervalo entre a operação HTTP e a atualização do cadastro do técnico.

**Limitação conhecida — dual write:** o evento é publicado depois do commit no banco. Se o RabbitMQ estiver indisponível, o chamado permanece salvo e a falha de publicação é registrada em log. O padrão Transactional Outbox seria uma evolução para aumentar a confiabilidade entre persistência e publicação.

## 9. Observabilidade

### 9.1. Rastreamento distribuído

OpenTelemetry instrumenta o FastAPI, as chamadas HTTP realizadas pelo HTTPX e a aplicação Java por meio do agente Java. Os traces são exportados via OTLP para o Jaeger.

Interface: `http://localhost:16686`

Um fluxo de atribuição permite acompanhar a requisição recebida pelo gateway, a API Python e a consulta HTTP ao serviço Java, conforme os spans instrumentados e propagados.

### 9.2. Métricas

O Prometheus coleta métricas dos seguintes alvos:

| Alvo | Endpoint de métricas |
|---|---|
| Serviço de chamados | `http://api-chamados:8000/metrics` |
| Serviço de técnicos | `http://api-tecnicos:8081/actuator/prometheus` |
| RabbitMQ | `http://rabbitmq:15692/metrics` |

Interface: `http://localhost:9090`

A configuração de scrape está em `observabilidade/prometheus.yml`.

### 9.3. Dashboards

O Grafana utiliza o Prometheus como fonte de dados e provisiona os dashboards presentes em `observabilidade/grafana/dashboards/`.

Interface: `http://localhost:3000`

Credenciais iniciais definidas no Compose: `admin` / `admin`. Altere essas credenciais antes de utilizar o ambiente fora de um contexto local/demonstrativo.

## 10. Persistência, volumes e configuração

Volumes nomeados:

- `dados-chamados`
- `dados-tecnicos`
- `dados-rabbitmq`
- `dados-prometheus`
- `dados-grafana`

As variáveis de ambiente são definidas em `.env`. O arquivo `.env.example` contém os nomes e valores de referência. Não versione credenciais reais.

O Compose configura as URLs internas dos bancos usando os nomes DNS dos containers. Por exemplo, a API Java utiliza `db-tecnicos:5432`, enquanto o acesso local de depuração é publicado em `127.0.0.1:5434`.

## 11. Script de dados de demonstração

O script `scripts/popular_banco.py` utiliza apenas a biblioteca padrão do Python 3.9+ e realiza operações pelas APIs do gateway, respeitando as validações e a publicação de eventos.

```bash
python scripts/popular_banco.py
python scripts/popular_banco.py --forcar
python scripts/popular_banco.py --url http://localhost:8080
```

O script cadastra técnicos e chamados de exemplo e simula etapas de atendimento. Sem `--forcar`, evita recriar chamados de demonstração já existentes.

## 12. Testes e validação

- Python: Pytest (`pytest`).
- Java: JUnit / testes do Spring Boot.
- Integração: validar chamadas entre os serviços, regras de disponibilidade e eventos RabbitMQ.
- Infraestrutura: validar healthchecks, persistência dos volumes e estado dos alvos do Prometheus.

Comandos úteis:

```bash
docker compose ps
docker compose logs -f api-chamados
docker compose logs -f api-tecnicos
docker compose logs -f rabbitmq
docker compose config
```

A validação operacional passo a passo está no [README principal](../README.md).

## 13. Tecnologias e versões de referência

| Tecnologia | Versão / referência no projeto |
|---|---|
| Python | 3.12 (imagem `python:3.12-slim`) |
| FastAPI | 0.115.12 |
| SQLAlchemy | 2.1.6 |
| Java | 21 |
| Spring Boot | 4.1.2 |
| PostgreSQL | 17 |
| RabbitMQ | 3.13 Management |
| NGINX | 1.27 Alpine |
| Jaeger | 2.22.0 |
| Prometheus | 3.5.0 |
| Grafana | 12.1.0 |
| OpenTelemetry Java Agent | 2.24.0 |

