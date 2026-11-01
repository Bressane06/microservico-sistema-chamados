# Sistema de Chamados — Microsserviços

Projeto acadêmico de Computação Distribuída para gerenciamento de chamados de suporte técnico. A solução utiliza dois microsserviços independentes, implementados em linguagens diferentes, com bancos de dados separados e comunicação via HTTP/REST.

## Sumário

1. [Arquitetura](#1-arquitetura)
2. [Tecnologias](#2-tecnologias)
3. [Pré-requisitos](#3-pré-requisitos)
4. [Estrutura do repositório](#4-estrutura-do-repositório)
5. [Modelo de dados](#5-modelo-de-dados)
6. [Microsserviço de chamados](#6-microsserviço-de-chamados)
7. [Microsserviço de técnicos](#7-microsserviço-de-técnicos)
8. [Configuração do ambiente](#8-configuração-do-ambiente)
9. [Docker e Docker Compose](#9-docker-e-docker-compose)
10. [Comunicação entre microsserviços](#10-comunicação-entre-microsserviços)
11. [Observabilidade](#11-observabilidade)
12. [Testes](#12-testes)
13. [Plano de desenvolvimento](#13-plano-de-desenvolvimento)
14. [Comandos úteis](#14-comandos-úteis)

---

## 1. Arquitetura

O sistema é composto por duas APIs independentes:

- **Microsserviço de chamados:** Python, FastAPI e SQLAlchemy.
- **Microsserviço de técnicos:** Java, Spring Boot e Spring Data JPA.
- **Persistência:** cada microsserviço possui seu próprio banco PostgreSQL.
- **Comunicação:** HTTP/REST entre as APIs.
- **Containers:** Docker e Docker Compose.
- **Observabilidade planejada:** OpenTelemetry, Jaeger, Prometheus e Grafana.
- **Testes planejados:** Pytest e JUnit.
- **Documentação:** Swagger/OpenAPI.

### Diagrama da arquitetura

```text
                  Cliente / Swagger UI
                          |
                      HTTP / REST
                          |
             +------------+------------+
             |                         |
      +------+-------+         +-------+------+
      | API Chamados |         | API Técnicos |
      | Python       | ------> | Java         |
      | FastAPI      |  HTTP   | Spring Boot  |
      +------+-------+         +-------+------+
             |                         |
      +------+-------+         +-------+------+
      | PostgreSQL A |         | PostgreSQL B |
      | Chamados     |         | Técnicos     |
      +--------------+         +--------------+

             Docker Compose
       Orquestração dos containers

       Observabilidade (planejada):
       OpenTelemetry + Jaeger
       Prometheus + Grafana
```

### Princípios da arquitetura

1. Cada microsserviço é responsável pelos próprios dados.
2. Um serviço não acessa diretamente o banco de dados do outro.
3. A comunicação entre os serviços ocorre por APIs HTTP.
4. Cada serviço pode ser construído e executado em seu próprio container.
5. Falhas de comunicação devem ser tratadas sem registrar atribuições incorretas.
6. O histórico das alterações dos chamados deve ser preservado.

## 2. Tecnologias

| Componente | Tecnologia |
|---|---|
| API de chamados | Python + FastAPI |
| Persistência Python | SQLAlchemy |
| API de técnicos | Java + Spring Boot |
| Persistência Java | Spring Data JPA + Hibernate |
| Bancos de dados | PostgreSQL |
| Comunicação | HTTP/REST |
| Containers | Docker + Docker Compose |
| Rastreamento distribuído | OpenTelemetry + Jaeger (pendente) |
| Métricas | Prometheus (pendente) |
| Dashboards | Grafana (pendente) |
| Testes Python | Pytest (pendente) |
| Testes Java | JUnit (pendente) |
| Documentação | Swagger / OpenAPI |
| Mensageria opcional | RabbitMQ |

## 3. Pré-requisitos

Ferramentas utilizadas no desenvolvimento:

- Docker Desktop com suporte a WSL 2.
- Python 3.12 ou versão compatível com as dependências.
- JDK 21.
- Visual Studio Code.
- Git para Windows.

Extensões recomendadas para o VS Code:

- Python e Pylance.
- Extension Pack for Java.
- Spring Boot Extension Pack.
- Docker.

Verifique as instalações no PowerShell:

```powershell
wsl --version
docker --version
docker compose version
python --version
java -version
javac -version
git --version
```

Teste o Docker:

```powershell
docker run --rm hello-world
```

O PostgreSQL é executado em containers, não sendo necessária sua instalação diretamente no Windows.

## 4. Estrutura do repositório

```text
sistema-chamados/
│
├── servico-chamados/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── routes/
│   │   │   └── chamados.py
│   │   └── services/
│   │       ├── tecnicos_client.py
│   │       └── historico.py
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── servico-tecnicos/
│   ├── src/
│   ├── pom.xml
│   └── Dockerfile
│
├── observabilidade/
│   └── prometheus.yml
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

### Arquivos importantes do serviço Python

- `main.py`: inicialização da aplicação FastAPI.
- `database.py`: conexão e gerenciamento das sessões do PostgreSQL.
- `models.py`: entidades Chamado e HistoricoChamado.
- `schemas.py`: schemas de validação e resposta.
- `routes/chamados.py`: endpoints de gerenciamento dos chamados.
- `services/tecnicos_client.py`: comunicação HTTP com o serviço Java.
- `services/historico.py`: registro das alterações dos chamados.

### Arquivos importantes do serviço Java

O serviço Java utiliza a organização em camadas:

- `entity`: entidades persistidas no banco.
- `repository`: acesso aos dados por Spring Data JPA.
- `service`: regras de negócio.
- `controller`: endpoints REST.
- `dto`: objetos de entrada e saída da API.

### .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
.pytest_cache/
.coverage

# Java
target/
*.class

# IDE
.vscode/
.idea/

# Ambiente e segredos
.env

# Logs
*.log
```

Não versione senhas reais. Mantenha um `.env.example` sem segredos e utilize `.env` localmente.

## 5. Modelo de dados

### 5.1. Chamados — PostgreSQL do serviço Python

| Campo | Descrição |
|---|---|
| id | Identificador do chamado |
| titulo | Título resumido do problema |
| descricao | Detalhes do problema |
| categoria | Categoria do chamado |
| prioridade | BAIXA, MEDIA, ALTA ou CRITICA |
| status | Estado atual do chamado |
| tecnico_id | Referência lógica ao técnico atribuído |
| criado_em | Data e hora da criação |
| atualizado_em | Data e hora da última atualização |

### 5.2. Histórico — PostgreSQL do serviço Python

A tabela `historico_chamados` registra as alterações realizadas nos chamados.

| Campo | Descrição |
|---|---|
| id | Identificador do histórico |
| chamado_id | Identificador do chamado relacionado |
| campo | Campo alterado |
| valor_anterior | Valor anterior |
| valor_novo | Novo valor |
| criado_em | Data e hora da alteração |

### 5.3. Técnicos — PostgreSQL do serviço Java

| Campo | Descrição |
|---|---|
| id | Identificador do técnico |
| nome | Nome do técnico |
| email | E-mail do técnico |
| especialidade | Especialidade principal |
| disponivel | Indica se pode receber chamados |
| ativo | Indica se o cadastro está ativo |
| criadoEm | Data de criação do cadastro |

### Independência dos bancos

O campo `tecnico_id` do chamado é uma referência lógica ao identificador gerenciado pelo serviço Java.

Não existe chave estrangeira entre tabelas de bancos pertencentes a microsserviços diferentes. A validação do técnico é realizada por meio da API Java.

## 6. Microsserviço de chamados

**Tecnologia:** Python + FastAPI + SQLAlchemy.

**Base URL (via gateway):** `http://localhost:8080`

### Endpoints implementados

| Método | Endpoint | Finalidade |
|---|---|---|
| POST | `/chamados` | Cadastrar chamado |
| GET | `/chamados` | Listar chamados |
| GET | `/chamados/{id}` | Consultar detalhes |
| PATCH | `/chamados/{id}` | Atualizar descrição, prioridade ou status |
| POST | `/chamados/{id}/cancelar` | Cancelar chamado |
| GET | `/chamados/{id}/historico` | Consultar histórico |
| POST | `/chamados/{id}/atribuir-tecnico` | Atribuir técnico por meio da API Java |

### Regras de negócio implementadas

- Validação dos dados de entrada com Pydantic.
- Cadastro de chamados com prioridade e status inicial.
- Consulta individual e listagem com filtros por status e categoria.
- Atualização de descrição, prioridade e status.
- Bloqueio de alterações em chamados encerrados.
- Impedimento de reabertura pela rota de atualização.
- Cancelamento de chamados.
- Registro das alterações no histórico.
- Validação do técnico por meio da comunicação HTTP com o serviço Java.

### Exemplo de cadastro

```http
POST /chamados
```

```json
{
  "titulo": "Computador sem internet",
  "descricao": "A conexão de rede não está funcionando.",
  "categoria": "Redes",
  "prioridade": "ALTA"
}
```

### Exemplo de atribuição de técnico

```http
POST /chamados/1/atribuir-tecnico
```

```json
{
  "tecnico_id": 2
}
```

A API Python consulta o serviço Java para validar o técnico. Após a confirmação, armazena o identificador no chamado e registra a alteração no histórico.

### Documentação interativa

`http://localhost:8080/docs`

## 7. Microsserviço de técnicos

**Tecnologia:** Java + Spring Boot + Spring Data JPA.

**Base URL (via gateway):** `http://localhost:8080`

### Endpoints implementados

| Método | Endpoint | Finalidade |
|---|---|---|
| POST | `/tecnicos` | Cadastrar técnico |
| GET | `/tecnicos` | Listar técnicos ativos |
| GET | `/tecnicos/{id}` | Consultar técnico |
| PUT | `/tecnicos/{id}` | Atualizar dados do técnico |
| DELETE | `/tecnicos/{id}` | Desativar técnico |
| GET | `/tecnicos/disponiveis` | Listar técnicos disponíveis |

O cadastro e a consulta de técnicos são utilizados também pelo microsserviço Python durante a atribuição de chamados.

### Regras implementadas

- Cadastro de técnicos.
- Validação de dados e e-mail.
- Consulta de técnicos.
- Atualização de dados cadastrais.
- Desativação lógica de técnicos.
- Consulta de técnicos disponíveis e ativos.

### Documentação

A documentação Swagger do Spring Boot depende da configuração da biblioteca springdoc-openapi.

Endereço esperado:

`http://localhost:8080/swagger-ui/index.html`

## 8. Configuração do ambiente

### 8.1. Ambiente virtual Python

No PowerShell:

```powershell
cd servico-chamados

python -m venv .venv

.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip

pip install fastapi "uvicorn[standard]" sqlalchemy "psycopg[binary]" pydantic-settings httpx pytest

pip freeze > requirements.txt
```

Se a ativação for bloqueada pelo PowerShell, utilize o CMD:

```cmd
.venv\Scripts\activate.bat
```

### 8.2. Projeto Spring Boot

Configuração utilizada no Spring Initializr:

- Project: Maven
- Language: Java
- Java: 21
- Group: `br.com.suporte`
- Artifact: `servico-tecnicos`
- Packaging: Jar

Dependências principais:

- Spring Web
- Spring Data JPA
- PostgreSQL Driver
- Validation
- Spring Boot Actuator

### 8.3. Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
POSTGRES_CHAMADOS_USER=chamados_user
POSTGRES_CHAMADOS_PASSWORD=senha_local_chamados
POSTGRES_CHAMADOS_DB=chamados_db

POSTGRES_TECNICOS_USER=tecnicos_user
POSTGRES_TECNICOS_PASSWORD=senha_local_tecnicos
POSTGRES_TECNICOS_DB=tecnicos_db
```

Esses valores são destinados ao desenvolvimento local. Não utilize essas senhas em produção e não versione o arquivo `.env`.

## 9. Docker e Docker Compose

O projeto possui configuração de Docker Compose para orquestrar os dois microsserviços e seus respectivos bancos PostgreSQL.

### Como executar (máquina limpa)

```bash
git clone <URL-DO-REPOSITORIO>
cd microservico-sistema-chamados

# Opcional: o compose possui valores padrão, mas o ideal é criar o seu .env
cp .env.example .env

docker compose up -d --build
docker compose ps        # aguarde todos os serviços em "healthy"
```

A primeira subida demora alguns minutos (build do Maven e download das imagens).

### Validação rápida

```bash
# Saúde do gateway
curl http://localhost:8080/health

# Cria um técnico (serviço Java) pelo gateway
curl -X POST http://localhost:8080/tecnicos \
  -H "Content-Type: application/json" \
  -d '{"nome":"Ana Souza","email":"ana@exemplo.com","especialidade":"Redes"}'

# Cria um chamado (serviço Python) pelo gateway
curl -X POST http://localhost:8080/chamados \
  -H "Content-Type: application/json" \
  -d '{"titulo":"Sem acesso à VPN","descricao":"Erro de autenticação","categoria":"Redes","prioridade":"ALTA"}'

# Atribui o técnico ao chamado (comunicação Python -> Java)
curl -X POST http://localhost:8080/chamados/1/atribuir-tecnico \
  -H "Content-Type: application/json" \
  -d '{"tecnico_id":1}'
```

Para encerrar: `docker compose down` (use `-v` para apagar também os dados).

### API Gateway (NGINX)

O NGINX (`gateway/nginx.conf`) é a única porta de entrada da aplicação. Os
microsserviços usam apenas `expose` no compose, ou seja, **não são acessíveis
diretamente do host**; o cliente não precisa conhecer a topologia interna.

| Rota no gateway | Destino |
|---|---|
| `/chamados/**`, `/docs`, `/openapi.json` | `api-chamados:8000` (Python / FastAPI) |
| `/tecnicos/**`, `/swagger-ui`, `/v3/api-docs` | `api-tecnicos:8081` (Java / Spring Boot) |
| `/health` | resposta do próprio gateway |

Se um serviço estiver fora do ar, o gateway responde `503` em JSON. Cada
requisição recebe um `X-Request-ID`, e o cabeçalho `traceparent` é repassado,
preservando o rastreamento distribuído no Jaeger.

### Portas expostas no host

| Componente | Endereço | Observação |
|---|---|---|
| **API Gateway** | http://localhost:8080 | entrada única da aplicação |
| Jaeger (traces) | http://localhost:16686 | observabilidade |
| Prometheus | http://localhost:9090 | métricas |
| Grafana | http://localhost:3000 | `admin` / `admin` |
| PostgreSQL de chamados | 127.0.0.1:5433 | somente local, para depuração |
| PostgreSQL de técnicos | 127.0.0.1:5434 | somente local, para depuração |

As APIs (`8000` e `8081`) permanecem acessíveis apenas dentro da rede Docker.

### Redes

- `rede-chamados`: comunicação entre a API de chamados e seu banco.
- `rede-tecnicos`: comunicação entre a API de técnicos e seu banco.
- `rede-servicos`: comunicação entre gateway, microsserviços e ferramentas de observabilidade.

### Volumes

- `dados-chamados`: persistência do banco de chamados.
- `dados-tecnicos`: persistência do banco de técnicos.

### Configuração do Spring Boot

No `application.properties`, a configuração local utiliza:

```properties
spring.application.name=servico-tecnicos

server.port=8081

spring.datasource.url=jdbc:postgresql://localhost:5434/tecnicos_db
spring.datasource.username=tecnicos_user
spring.datasource.password=senha_local_tecnicos

spring.jpa.hibernate.ddl-auto=update
spring.jpa.show-sql=true
spring.jpa.properties.hibernate.format_sql=true
```

No Docker Compose, as variáveis de ambiente sobrescrevem a URL de conexão para utilizar o nome do container do banco:

`jdbc:postgresql://db-tecnicos:5432/tecnicos_db`

### Estado da infraestrutura

- [x] Docker Compose com todos os serviços e bancos.
- [x] Dois bancos PostgreSQL isolados, com healthcheck e volumes.
- [x] Redes independentes por serviço e rede compartilhada.
- [x] API Gateway (NGINX) como entrada única.
- [x] Healthcheck das APIs e do gateway (o gateway só sobe com as APIs saudáveis).
- [x] Versões de imagem fixadas (Prometheus, Grafana, NGINX, PostgreSQL).
- [ ] Validar a execução completa em uma máquina limpa.

## 10. Comunicação entre microsserviços

A comunicação entre os serviços ocorre por HTTP/REST.

### Fluxo de atribuição de técnico

1. O cliente envia uma solicitação para a API Python.
2. A API Python consulta a API Java por meio do cliente HTTP `tecnicos_client.py`.
3. A API Java consulta seu próprio banco PostgreSQL.
4. O serviço Java retorna os dados do técnico.
5. A API Python verifica se o técnico está ativo e disponível.
6. Se a validação for aprovada, o Python atualiza o `tecnico_id` do chamado.
7. A alteração é registrada no histórico do chamado.

### Exemplo da comunicação

```text
Cliente
   |
   | POST /chamados/1/atribuir-tecnico
   |
   v
API Python (FastAPI)
   |
   | GET /tecnicos/2
   |
   v
API Java (Spring Boot)
   |
   | Consulta
   v
PostgreSQL Técnicos
   |
   | Retorna dados do técnico
   v
API Java
   |
   | Resposta HTTP
   v
API Python
   |
   | Atualiza chamado e histórico
   v
PostgreSQL Chamados
```

### Tratamento de falhas

O cliente HTTP utiliza timeout para evitar esperas indefinidas.

- Técnico não encontrado: retorno HTTP 404.
- Técnico indisponível ou inativo: retorno HTTP 409.
- Erro na resposta do serviço Java: retorno HTTP 502.
- Serviço Java inacessível: retorno HTTP 503.

A API Python não deve registrar uma atribuição quando não houver confirmação da validação do técnico.

**Evolução planejada:** atualizar também a disponibilidade do técnico no serviço Java após uma atribuição, impedindo que ele receba múltiplos chamados simultaneamente, conforme a regra de negócio definida.

Como são dois bancos, não existe uma única transação SQL capaz de reverter automaticamente alterações nos dois serviços. Futuramente, podem ser implementadas operações de compensação ou mensageria.

### Mensageria opcional

RabbitMQ poderá ser adicionado posteriormente para comunicação assíncrona, como notificações de abertura, atualização e encerramento de chamados.

## 11. Observabilidade

A observabilidade será implementada após a validação da infraestrutura e da integração entre as APIs.

| Ferramenta | Responsabilidade |
|---|---|
| OpenTelemetry | Instrumentação e exportação de traces e métricas |
| Jaeger | Visualização de rastreamento distribuído |
| Prometheus | Coleta e armazenamento de métricas |
| Grafana | Dashboards e visualização das métricas |

### Métricas sugeridas

- Requisições por microsserviço.
- Latência das APIs.
- Taxa de erros HTTP.
- Duração da comunicação Python → Java.
- Quantidade de chamados por status.
- Quantidade de técnicos disponíveis.
- Falhas nas solicitações de atribuição.

### Rastreamento distribuído

Um trace da atribuição de técnico deverá permitir observar operações como:

```text
POST /chamados/{id}/atribuir-tecnico
    |
    +-- Consultar técnico (Java)
    |
    +-- Validar disponibilidade
    |
    +-- Atualizar chamado (Python)
    |
    +-- Registrar histórico (Python)
```

## 12. Testes

As ferramentas previstas são Pytest para Python e JUnit para Java.

### Chamados

- [ ] Cadastro válido e validação de dados inválidos.
- [ ] Consulta da lista e dos detalhes.
- [ ] Atualização de descrição, prioridade e status.
- [ ] Cancelamento conforme as regras do sistema.
- [ ] Registro e consulta do histórico.

### Técnicos

- [ ] Cadastro e consulta de técnicos.
- [ ] Atualização de dados.
- [ ] Desativação de técnicos.
- [ ] Consulta de técnicos disponíveis.
- [ ] Validação de técnicos inativos.

### Integração distribuída

- [x] Comunicação HTTP entre Python e Java.
- [x] Consulta e validação de técnico.
- [x] Atribuição de técnico ao chamado.
- [x] Registro da atribuição no histórico.
- [ ] Atualização da disponibilidade do técnico após atribuição.
- [ ] Teste de técnico indisponível.
- [ ] Teste de API Java fora do ar ou com timeout.
- [ ] Teste de falha parcial durante a atribuição.
- [ ] Teste de requisições concorrentes para o mesmo técnico.

## 13. Plano de desenvolvimento

### Fase 1 — Preparação

- [x] Criar repositório e diretórios.
- [x] Configurar ambiente Python.
- [x] Gerar projeto Spring Boot.
- [x] Configurar dependências principais.

### Fase 2 — Microsserviço Java

- [x] Criar entidade, repository, service e controller de técnicos.
- [x] Implementar operações CRUD.
- [x] Conectar ao PostgreSQL de técnicos.
- [x] Executar e testar a API localmente.

### Fase 3 — Microsserviço Python

- [x] Criar models, schemas, rotas e serviços.
- [x] Implementar operações de gerenciamento de chamados.
- [x] Conectar ao PostgreSQL de chamados.
- [x] Implementar histórico de alterações.
- [x] Executar e testar a API localmente.

### Fase 4 — Integração

- [x] Implementar cliente HTTP Python → Java.
- [x] Implementar atribuição de técnico.
- [x] Tratar erros de comunicação e validação.
- [x] Registrar atribuição no histórico.
- [ ] Atualizar disponibilidade do técnico após atribuição.
- [ ] Testar falhas e concorrência.

### Fase 5 — Docker

- [x] Criar configuração inicial dos serviços e bancos.
- [x] Configurar Docker Compose.
- [x] Configurar healthchecks, volumes e redes.
- [ ] Validar execução completa das aplicações em containers.
- [ ] Validar comunicação entre APIs dentro do Docker.

### Fase 6 — Observabilidade e entrega

- [ ] Adicionar OpenTelemetry e Jaeger.
- [ ] Configurar Prometheus e Grafana.
- [ ] Completar testes automatizados.
- [ ] Documentar arquitetura e decisões técnicas.
- [ ] Preparar a demonstração do sistema.

## 14. Comandos úteis

### Python

Ativar ambiente virtual:

```powershell
cd servico-chamados
.\.venv\Scripts\Activate.ps1
```

Executar API:

```powershell
uvicorn app.main:app --reload
```

### Java

Executar API:

```powershell
cd servico-tecnicos
.\mvnw.cmd spring-boot:run
```

### Docker

Validar configuração:

```powershell
docker compose config
```

Construir e iniciar:

```powershell
docker compose up --build -d
```

Listar containers:

```powershell
docker compose ps
```

Ver logs:

```powershell
docker compose logs -f
```

Ver logs de um serviço:

```powershell
docker compose logs -f api-chamados
docker compose logs -f api-tecnicos
```

Parar containers:

```powershell
docker compose down
```

Parar e apagar volumes:

```powershell
docker compose down -v
```

**Atenção:** `docker compose down -v` remove os volumes e os dados persistidos dos bancos.

### URLs locais

| Serviço | Endereço |
|---|---|
| Swagger FastAPI | http://localhost:8080/docs |
| API Spring Boot | http://localhost:8080/tecnicos |
| Swagger Spring Boot | http://localhost:8080/swagger-ui/index.html |

---

## Referências oficiais

- Docker Desktop
- Docker Compose
- FastAPI
- SQLAlchemy
- Spring Initializr
- Spring Boot
- PostgreSQL
- OpenTelemetry
- Jaeger
- Prometheus
- Grafana

---

**Status do projeto:** microsserviços Python e Java implementados e executados localmente, com comunicação HTTP entre as APIs e atribuição de técnicos registrada no histórico dos chamados. A integração funcional foi testada. A validação completa da execução em Docker, a atualização da disponibilidade dos técnicos e a observabilidade permanecem como próximas etapas.
