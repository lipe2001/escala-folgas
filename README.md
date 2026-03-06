# Escala de Folgas (NOC)

Aplicação para gerenciar escala de plantão/férias com:
- **API FastAPI** para operações públicas e administrativas.
- **Front-end server-side** com Jinja2 para operação web.
- **Geração automática** de propostas de folga baseada em regras de capacidade.
- **Integração com Telegram** para notificação de publicação.

---

## 1) Visão geral da solução

A aplicação concentra o fluxo de escala em três blocos:

1. **Cadastro e operação**
   - Funcionários (`employees`), finais de semana (`weekends`) e alocações de domingo (`sunday_assignments`).
2. **Geração**
   - Criação de lote (`generation_batches`) e proposta de folgas (`dayoff_proposals`) via heurística no serviço `generator`.
3. **Publicação**
   - Aprovação/publicação de lote e envio de mensagens no Telegram.

---

## 2) Stack e dependências

- Python 3.11
- FastAPI + Uvicorn
- PostgreSQL (via `psycopg` / `psycopg_pool`)
- Jinja2 (templates web)
- python-telegram-bot
- JWT (PyJWT)

Dependências estão em `requirements.txt`.

> ⚠️ Observação: atualmente `requirements.txt` está com `PyJWTDATABASE_URL` em uma única linha, o que indica erro de formatação. Recomenda-se corrigir para `PyJWT` em linha separada.

---

## 3) Estrutura do projeto

```text
app/
  main.py                 # bootstrap da API e startup do bot
  settings.py             # configurações via variáveis de ambiente
  db.py                   # pool e helpers SQL
  auth_handler.py         # emissão e validação JWT
  deps.py                 # dependências de autorização
  schemas.py              # payloads pydantic
  routers/
    public.py             # endpoints públicos (consulta/ICS)
    admin.py              # endpoints administrativos (JWT)
    web.py                # páginas HTML e fluxos web
  services/
    generator.py          # regra de geração de folgas
  repository/
    *.py                  # DAOs
  frontend/
    pages/, components/, static/
  bot/
    bot.py                # handlers e disparo Telegram
    data.csv              # inscritos no bot
docker-compose.yml
Dockerfile
```

---

## 4) Variáveis de ambiente

Crie um arquivo `.env` na raiz (baseado em `exemple.env`):

```env
DATABASE_URL=postgresql://usuario:senha@host:5432/database
SECRET_KEY=sua_chave_jwt
ADMIN_ROLES=supervisor,admin
ADMIN=admin
ADMIN_PASSWORD=senha_forte
TELEGRAM_TOKEN=seu_token_do_bot
```

### Significado
- `DATABASE_URL`: conexão PostgreSQL.
- `SECRET_KEY`: assinatura JWT.
- `ADMIN` / `ADMIN_PASSWORD`: login administrativo.
- `TELEGRAM_TOKEN`: token do bot no Telegram.
- `ADMIN_ROLES`: mantido por compatibilidade (o fluxo atual valida `ADMIN`).

---

## 5) Banco de dados (pré-requisito)

A aplicação espera tabelas já existentes para:
- `employees`
- `weekends`
- `sunday_assignments`
- `generation_batches`
- `dayoff_proposals`
- `dayoffs`

Atualmente o repositório **não inclui migrações/versionamento de schema**. Se necessário, recomenda-se introduzir Alembic para padronizar criação/alteração de banco.

---

## 6) Como rodar localmente

## Opção A — Docker Compose (mais simples)

1. Crie e preencha `.env`.
2. Suba o container:

```bash
docker compose up --build -d
```

3. Acesse:
- App/API: `http://localhost:8000`
- Docs OpenAPI: `http://localhost:8000/docs`

## Opção B — Python local (sem Docker)

1. Crie ambiente virtual e instale dependências:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure `.env`.
3. Garanta PostgreSQL disponível com schema esperado.
4. Suba a aplicação:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 7) Fluxo funcional recomendado

1. Criar fim de semana (`POST /admin/weekends`).
2. Definir alocação de domingo (`PUT /admin/weekends/{id}/sunday-assignments`).
3. Gerar lote (`POST /admin/weekends/{id}/generate`).
4. Revisar propostas (`GET /admin/batches/{batch_id}`).
5. Aprovar (`POST /admin/batches/{batch_id}/approve`).
6. Publicar (`POST /admin/batches/{batch_id}/publish`).
7. Após publicar, o bot envia notificações configuradas.

---

## 8) Principais rotas

### Públicas
- `GET /public/folgas?start=YYYY-MM-DD&end=YYYY-MM-DD`
- `GET /public/folgas/week?position=0`
- `GET /public/folgas.ics?start=...&end=...&team=...&role=...`

### Administrativas (JWT)
- `POST /login` (retorna token)
- `GET /admin/employees`
- `POST /admin/weekends`
- `PUT /admin/weekends/{weekend_id}/sunday-assignments`
- `POST /admin/weekends/{weekend_id}/generate`
- `POST /admin/batches/{batch_id}/approve`
- `POST /admin/batches/{batch_id}/publish`

### Web
- `/` e páginas em `/weekend`, `/employees`, etc.

---

## 9) Avaliação técnica (pontos positivos e negativos)

## Pontos positivos
- **Boa separação por camadas** (`routers`, `services`, `repository`).
- **Uso de SQL parametrizado** (`%s`) reduz risco de SQL injection.
- **Geração de escala encapsulada** no serviço `generator`, facilitando evolução da regra.
- **API pública com exportação ICS**, útil para consumo em calendário.
- **Integração Telegram** já funcionando como mecanismo de comunicação.

## Pontos de atenção / negativos
- **Sem migrations** de banco no repositório, dificultando onboarding e reprodutibilidade.
- **Cobertura de testes ausente** (unitários/integrados/e2e).
- **Tratamento de erros genérico** (`except:` em alguns pontos) reduz observabilidade.
- **Duplicação de regra de acesso a dados** entre `routers` e `repository`.
- **Alguns bugs pontuais de implementação**, por exemplo:
  - Uso de `tuple(team)` em consultas (deveria ser `(team,)`).
  - Publicação usa `id` retornado em lista/tupla para `send_week`, potencialmente incorreto.
  - Dependências com formatação inválida em `requirements.txt`.
- **Segurança**: validação de `Authorization` pode ser mais robusta (prefixo `Bearer`, mensagens e status mais precisos).

## Melhorias recomendadas (prioridade)

### Curto prazo (alto impacto)
1. Corrigir bugs de parâmetros SQL e fluxo de publicação.
2. Corrigir `requirements.txt`.
3. Adicionar logs estruturados e tratamento explícito de exceções.
4. Criar script/migrações de banco (Alembic).

### Médio prazo
1. Introduzir testes automatizados (pytest):
   - unitários para `generator.py`
   - integração para rotas admin/public
2. Padronizar DAOs para evitar SQL espalhado em múltiplas camadas.
3. Tipar respostas com `response_model` (Pydantic) nas rotas.

### Longo prazo
1. Pipeline CI (lint + testes + build).
2. Controle de permissões com RBAC real (aproveitando `ADMIN_ROLES`).
3. Auditoria de publicação/reversão de lotes.

---

## 10) Autenticação

### Login
`POST /login` com JSON:

```json
{
  "username": "admin",
  "password": "senha"
}
```

Retorno:

```json
{
  "token": "<jwt>"
}
```

Use no header:

```http
Authorization: <jwt>
```

> Sugestão futura: padronizar para `Authorization: Bearer <jwt>`.

---

## 11) Telegram bot

- Comando `/start`: mensagem inicial.
- Comando `/subscribe`: registra `chat_id` em `app/bot/data.csv`.
- Ao publicar lote, dispara:
  - resumo semanal de folgas
  - escala de fim de semana/domingo

---

## 12) Troubleshooting

- **Erro de conexão com banco**: valide `DATABASE_URL` e acesso de rede.
- **Token inválido/expirado**: faça novo login em `/login`.
- **Bot não envia mensagem**: valide `TELEGRAM_TOKEN` e se o usuário fez `/subscribe`.
- **Falha ao subir local**: revisar dependências (`requirements.txt`) e versão Python.
