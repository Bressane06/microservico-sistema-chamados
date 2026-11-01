# Sistema de Chamados — Microsserviços

Sistema distribuído para gerenciamento de chamados de suporte técnico, desenvolvido para a disciplina de Computação Distribuída. A aplicação utiliza dois microsserviços independentes (Python e Java), bancos PostgreSQL separados, comunicação HTTP e mensageria RabbitMQ.

A arquitetura também inclui API Gateway (NGINX) e ferramentas de observabilidade (OpenTelemetry, Jaeger, Prometheus e Grafana).

## Tecnologias

- **Chamados:** Python 3.12, FastAPI e SQLAlchemy.
- **Técnicos:** Java 21, Spring Boot e Spring Data JPA.
- **Persistência:** PostgreSQL 17 (um banco por microsserviço).
- **Gateway:** NGINX.
- **Mensageria:** RabbitMQ.
- **Observabilidade:** OpenTelemetry, Jaeger, Prometheus e Grafana.
- **Orquestração:** Docker e Docker Compose.

## Pré-requisitos

Antes de começar, instale e inicie:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) com Docker Compose v2.
- Git (para clonar o repositório).
- Um terminal: PowerShell, Windows Terminal, Bash ou equivalente.

Não é necessário instalar Python, Java ou PostgreSQL para executar a aplicação em containers. O Docker realiza o build das imagens e executa os bancos e serviços.

Verifique as instalações:

```bash
docker --version
docker compose version
git --version
```

## Instalação e execução

### 1. Obter o repositório

```bash
git clone https://github.com/Bressane06/microservico-sistema-chamados.git
cd microservico-sistema-chamados
```

Se você já possui o projeto localmente, entre na pasta raiz — aquela que contém `docker-compose.yml`.

### 2. Configurar as variáveis de ambiente

Crie o arquivo `.env` a partir do modelo.

O arquivo `.env.example` já contém os nomes das variáveis necessários. Para uma execução local de demonstração, os valores padrão funcionam. Antes de expor o ambiente em uma rede, altere as senhas e não compartilhe o arquivo `.env`.

Variáveis utilizadas:

| Variável                     | Finalidade                   |
| ---------------------------- | ---------------------------- |
| `POSTGRES_CHAMADOS_USER`     | Usuário do banco de chamados |
| `POSTGRES_CHAMADOS_PASSWORD` | Senha do banco de chamados   |
| `POSTGRES_CHAMADOS_DB`       | Nome do banco de chamados    |
| `POSTGRES_TECNICOS_USER`     | Usuário do banco de técnicos |
| `POSTGRES_TECNICOS_PASSWORD` | Senha do banco de técnicos   |
| `POSTGRES_TECNICOS_DB`       | Nome do banco de técnicos    |
| `RABBITMQ_USER`              | Usuário do RabbitMQ          |
| `RABBITMQ_PASSWORD`          | Senha do RabbitMQ            |

### 3. Validar a configuração do Compose

Na raiz do projeto, execute:

```bash
docker compose config
```

Se o comando terminar sem erros, a configuração foi interpretada corretamente.

### 4. Construir as imagens e iniciar os containers

```bash
docker compose up --build -d
```

Na primeira execução, o Docker precisará baixar as imagens-base e construir os serviços. Isso pode levar alguns minutos.

O Compose inicia:

- API Gateway (NGINX);
- API de chamados e PostgreSQL de chamados;
- API de técnicos e PostgreSQL de técnicos;
- RabbitMQ;
- Jaeger;
- Prometheus;
- Grafana.

As APIs aguardam os respectivos bancos e o RabbitMQ conforme as dependências e healthchecks definidos no Compose. O gateway aguarda as duas APIs ficarem saudáveis.

### 5. Verificar os containers

```bash
docker compose ps
```

Aguarde os serviços de aplicação e o gateway apresentarem estado `healthy`. O primeiro início do serviço Java pode demorar mais devido à inicialização do Spring Boot.

Se algum serviço não iniciar, consulte os logs:

```bash
docker compose logs -f
```

Para acompanhar um componente específico:

```bash
docker compose logs -f api-chamados
docker compose logs -f api-tecnicos
docker compose logs -f api-gateway
docker compose logs -f rabbitmq
```

### 6. Validar a aplicação

O ponto de entrada das APIs é o gateway: `http://localhost:8080`.

**Verificar a saúde do gateway:**

```bash
curl http://localhost:8080/health
```

Resposta esperada:

```json
{
  "status": "ok",
  "servico": "api-gateway"
}
```

**Verificar a documentação e os serviços:**

- FastAPI / Swagger: http://localhost:8080/docs
- Spring Boot / Swagger: http://localhost:8080/swagger-ui/index.html
- OpenAPI do FastAPI: http://localhost:8080/openapi.json
- OpenAPI do Spring: http://localhost:8080/v3/api-docs

**Testar o cadastro de técnico:**

```bash
curl -X POST http://localhost:8080/tecnicos \
  -H "Content-Type: application/json" \
  -d '{"nome":"Ana Souza","email":"ana.souza@exemplo.com","especialidade":"Redes"}'
```

**Testar o cadastro de chamado:**

```bash
curl -X POST http://localhost:8080/chamados \
  -H "Content-Type: application/json" \
  -d '{"titulo":"Sem acesso à VPN","descricao":"Erro de autenticação ao conectar na VPN.","categoria":"Redes","prioridade":"ALTA"}'
```

Os exemplos acima retornam os registros criados, incluindo seus identificadores. Utilize os IDs retornados nos próximos testes.

**Testar a listagem:**

```bash
curl http://localhost:8080/tecnicos
curl http://localhost:8080/chamados
```

**Testar a atribuição de técnico:**

Substitua `1` pelos IDs válidos retornados nos cadastros:

```bash
curl -X POST http://localhost:8080/chamados/1/atribuir-tecnico \
  -H "Content-Type: application/json" \
  -d '{"tecnico_id":1}'
```

A API de chamados consulta o serviço de técnicos para verificar se o técnico existe, está ativo e disponível. Após a confirmação, o chamado é atualizado e um evento é publicado no RabbitMQ. A disponibilidade do técnico é atualizada de forma assíncrona; aguarde alguns segundos antes de consultar novamente:

```bash
curl http://localhost:8080/tecnicos/1
```

### 7. (Opcional) Popular com dados de demonstração

Com os containers em execução, e tendo Python 3.9 ou superior instalado no computador, execute na raiz do projeto:

```bash
python scripts/popular_banco.py
```

Para criar novamente os chamados de exemplo:

```bash
python scripts/popular_banco.py --forcar
```

O script utiliza as APIs pelo gateway, não grava diretamente nos bancos.

### 8. Acessar as ferramentas de observabilidade

| Ferramenta          | Endereço               | Acesso                           |
| ------------------- | ---------------------- | -------------------------------- |
| Jaeger              | http://localhost:16686 | Visualização de traces           |
| Prometheus          | http://localhost:9090  | Métricas e estado dos targets    |
| Grafana             | http://localhost:3000  | `admin` / `admin` (padrão local) |
| RabbitMQ Management | http://localhost:15672 | Credenciais definidas no `.env`  |

No Prometheus, acesse **Status → Targets** para verificar se os alvos estão sendo coletados. No Grafana, consulte o dashboard provisionado do sistema. No RabbitMQ, a aba **Queues** permite acompanhar as filas criadas para os eventos de chamados.

## Portas utilizadas

| Componente            | Porta no host | Observação                         |
| --------------------- | ------------: | ---------------------------------- |
| API Gateway           |        `8080` | Entrada das APIs                   |
| PostgreSQL — chamados |        `5433` | Vinculado a `127.0.0.1`, uso local |
| PostgreSQL — técnicos |        `5434` | Vinculado a `127.0.0.1`, uso local |
| RabbitMQ Management   |       `15672` | Painel administrativo              |
| Jaeger UI             |       `16686` | Rastreamento                       |
| Jaeger OTLP gRPC      |        `4317` | Recepção de traces                 |
| Jaeger OTLP HTTP      |        `4318` | Recepção OTLP                      |
| Prometheus            |        `9090` | Métricas                           |
| Grafana               |        `3000` | Dashboards                         |

As portas `8000` (FastAPI) e `8081` (Spring Boot) são internas à rede Docker. A comunicação externa com as APIs deve ser feita pela porta `8080` do gateway.

## Encerrar a aplicação

Para parar e remover os containers e as redes criadas pelo Compose, preservando os dados dos volumes:

```bash
docker compose down
```

Para também apagar os dados persistidos dos bancos, RabbitMQ, Prometheus e Grafana:

```bash
docker compose down -v
```

> **Atenção:** `docker compose down -v` remove os volumes nomeados e apaga os dados persistidos. Utilize somente quando quiser reiniciar o ambiente do zero.

## Documentação técnica

A documentação detalhada da arquitetura, dos modelos de dados, dos endpoints, das regras de negócio, da comunicação HTTP/RabbitMQ e da observabilidade está em [`doc/tecnica.md`](doc/tecnica.md).

## Estrutura resumida

```text
.
├── README.md
├── doc/
│   └── tecnica.md
├── docker-compose.yml
├── .env.example
├── gateway/
├── observabilidade/
├── scripts/
├── servico-chamados/
└── servico-tecnicos/
```

atualmente já tem um readme, atualize ele com os valores/estrutura atual, depois renomeie para doc/tecnica e crie um outro readme para ter isso: "O repositório deve conter um guia claro de instalação e execução no arquivo README.md (passo a passo para subida dos contêineres e validação da aplicação)"
