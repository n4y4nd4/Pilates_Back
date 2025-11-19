# Sistema de Cobrança Automatizada - Pilates

Sistema Django REST Framework para gerenciamento automatizado de cobranças de clientes de Pilates, com notificações via E-mail e WhatsApp.

## 📋 Índice

- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [API Endpoints](#api-endpoints)
- [Testes](#testes)
- [Integração com React](#integração-com-react)
- [Arquitetura](#arquitetura)

## ✨ Funcionalidades

### Core
- ✅ **CRUD Completo de Clientes**: Cadastro, listagem, atualização e exclusão
- ✅ **CRUD de Cobranças**: Gerenciamento de cobranças com status (Pendente, Pago, Atrasado, Cancelado)
- ✅ **Geração Automática de Cobrança**: Ao cadastrar um novo cliente, a primeira cobrança é criada automaticamente
- ✅ **Cálculo Inteligente de Datas**: Próxima data de vencimento sempre no futuro

### Notificações
- ✅ **E-mail Automático**: Envio via SMTP (Gmail configurado)
- ✅ **WhatsApp via Meta API**: Integração com WhatsApp Business Cloud API
- ✅ **Kill Switch**: Controle independente para desativar WhatsApp sem afetar E-mail
- ✅ **Régua de Notificações**:
  - **D-3**: Lembrete 3 dias antes do vencimento
  - **D+1**: Aviso de atraso 1 dia após vencimento
  - **D+10**: Aviso de bloqueio 10 dias após vencimento
  - **D+N**: Avisos genéricos para atrasos maiores

### Agendamento
- ✅ **Rotina Diária Automática**: Executa diariamente às 00:01
  - Marca cobranças vencidas como "Atrasado"
  - Identifica cobranças elegíveis para notificação
  - Dispara notificações via E-mail e WhatsApp
  - Registra todas as tentativas de envio na tabela `Notificacao`

## 🛠 Tecnologias

- **Django 5.2.7**: Framework web Python
- **Django REST Framework 3.16.1**: API REST
- **Django-APScheduler 0.7.0**: Agendamento de tarefas
- **django-cors-headers**: CORS para integração com frontend React
- **SQLite**: Banco de dados (desenvolvimento)
- **Gmail SMTP**: Envio de e-mails
- **Meta Cloud API**: Envio de mensagens WhatsApp

## 📁 Estrutura do Projeto

```
Projeto_Extensao/
├── cobranca_app/              # Aplicativo principal
│   ├── core/                  # Módulo core (constantes, exceções, utils)
│   │   ├── constants.py       # Enums e constantes
│   │   ├── exceptions.py      # Exceções customizadas
│   │   ├── utils.py           # Funções utilitárias
│   │   └── validators.py      # Validações
│   ├── services/              # Camada de serviços (lógica de negócio)
│   │   ├── billing_service.py      # Operações de cobrança
│   │   ├── cliente_service.py      # Operações de cliente
│   │   ├── email_service.py        # Envio de e-mail
│   │   ├── whatsapp_service.py     # Envio de WhatsApp
│   │   ├── notification_service.py # Gerenciamento de notificações
│   │   ├── message_builder.py      # Construção de mensagens
│   │   └── cobranca_service.py     # Rotina diária (orquestração)
│   ├── models.py              # Modelos de dados
│   ├── views.py               # Views da API (HTTP handlers)
│   ├── serializers.py         # Serializers DRF
│   ├── urls.py                # URLs da API
│   ├── tasks.py               # Tarefas agendadas
│   ├── tests/                 # Testes automatizados
│   │   ├── test_models.py     # Testes de modelos
│   │   ├── test_services.py   # Testes de serviços
│   │   ├── test_api.py        # Testes de API
│   │   └── test_utils.py      # Testes de utilitários
│   └── management/commands/   # Comandos Django
│       ├── startjobs.py       # Iniciar agendador
│       └── test_email.py      # Testar envio de e-mail
├── pilates_cobranca/          # Configurações do projeto Django
│   ├── settings.py            # Configurações (CORS, E-mail, WhatsApp)
│   ├── urls.py                # URLs principais
│   └── wsgi.py                # WSGI config
├── manage.py                  # Script de gerenciamento Django
├── requirements.txt           # Dependências Python
└── README.md                  # Este arquivo
```

## 🚀 Instalação

### Pré-requisitos

- Python 3.8+
- pip
- Conta Gmail (para envio de e-mails)
- Conta Meta Business (para WhatsApp - opcional)

### Passos

1. **Clone o repositório** (ou navegue até a pasta do projeto)

2. **Crie um ambiente virtual**:
```bash
python -m venv venv
```

3. **Ative o ambiente virtual**:
   - **Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Linux/Mac**:
     ```bash
     source venv/bin/activate
     ```

4. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

5. **Execute as migrações**:
```bash
python manage.py migrate
```

6. **Crie um superusuário** (opcional, para acessar o admin):
```bash
python manage.py createsuperuser
```

## ⚙️ Configuração

### 1. Configuração de E-mail (Gmail)

Edite `pilates_cobranca/settings.py`:

```python
EMAIL_HOST_USER = 'seu_email@gmail.com'
EMAIL_HOST_PASSWORD = 'sua_senha_de_app'  # Use "Senha de App" do Gmail
DEFAULT_FROM_EMAIL = 'seu_email@gmail.com'
```

**Como obter Senha de App do Gmail:**
1. Acesse: https://myaccount.google.com/apppasswords
2. Gere uma nova senha de app
3. Use essa senha no `EMAIL_HOST_PASSWORD`

### 2. Configuração de WhatsApp (Meta API)

Edite `pilates_cobranca/settings.py`:

```python
META_API_SETTINGS = {
    'TOKEN': 'SEU_TOKEN_AQUI',
    'PHONE_ID': 'SEU_PHONE_ID_AQUI',
    'URL_BASE': 'https://graph.facebook.com/v22.0/',
    'MOCK_MODE': False,
    'WHATSAPP_ENABLED': True,  # Kill Switch: False para desativar
}
```

**Kill Switch**: Defina `WHATSAPP_ENABLED: False` para desativar envio de WhatsApp sem afetar E-mail.

### 3. Configuração CORS (para React)

O CORS já está configurado para aceitar requisições de:
- `http://localhost:3000`
- `http://localhost:3001`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:3001`

Para adicionar outros domínios, edite `pilates_cobranca/settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://seu-dominio.com",
]
```

## 📖 Uso

### Iniciar o servidor de desenvolvimento

```bash
python manage.py runserver
```

O servidor estará disponível em: `http://localhost:8000`

### Iniciar o agendador de tarefas

Em um terminal separado:

```bash
python manage.py startjobs
```

Isso iniciará o agendador que executa a rotina diária às 00:01.

### Testar envio de e-mail

```bash
python manage.py test_email
```

## 🔌 API Endpoints

### Base URL: `http://localhost:8000/api/`

### Clientes

- **GET** `/api/clientes/` - Lista todos os clientes
- **POST** `/api/clientes/` - Cria um novo cliente (gera cobrança automaticamente)
- **GET** `/api/clientes/{id}/` - Detalhes de um cliente
- **PATCH** `/api/clientes/{id}/` - Atualiza um cliente
- **DELETE** `/api/clientes/{id}/` - Remove um cliente

**Exemplo de criação:**
```json
POST /api/clientes/
{
  "plano": 1,
  "nome": "João Silva",
  "cpf": "12345678901",
  "telefone_whatsapp": "5521999999999",
  "email": "joao@example.com",
  "data_inicio_contrato": "2025-01-20",
  "status_cliente": "ATIVO"
}
```

### Cobranças

- **GET** `/api/cobrancas/` - Lista todas as cobranças
- **GET** `/api/cobrancas/{id}/` - Detalhes de uma cobrança
- **PATCH** `/api/cobrancas/{id}/marcar_pago/` - Marca cobrança como paga

**Exemplo de marcar como pago:**
```bash
PATCH /api/cobrancas/1/marcar_pago/
```

### Planos

- **GET** `/api/planos/` - Lista planos ativos (somente leitura)

## 🧪 Testes

Execute todos os testes:

```bash
python manage.py test
```

Execute testes específicos:

```bash
python manage.py test cobranca_app.tests.test_models
python manage.py test cobranca_app.tests.test_services
python manage.py test cobranca_app.tests.test_api
python manage.py test cobranca_app.tests.test_utils
```

## ⚛️ Integração com React

O projeto está preparado para integração com frontend React.

### Configuração no React

1. **Instale axios** (ou use fetch):
```bash
npm install axios
```

2. **Configure a base URL**:
```javascript
// api.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
```

3. **Exemplo de uso**:
```javascript
// Listar clientes
const clientes = await api.get('/clientes/');

// Criar cliente
const novoCliente = await api.post('/clientes/', {
  plano: 1,
  nome: 'João Silva',
  cpf: '12345678901',
  telefone_whatsapp: '5521999999999',
  email: 'joao@example.com',
  data_inicio_contrato: '2025-01-20',
  status_cliente: 'ATIVO'
});

// Marcar cobrança como paga
await api.patch(`/cobrancas/${id}/marcar_pago/`);
```

### CORS

O CORS está configurado para aceitar requisições de `localhost:3000` e `localhost:3001`. Se usar outra porta, adicione em `settings.py`.

## 🏗 Arquitetura

O projeto segue os princípios de **Clean Code**:

### Separação de Responsabilidades

- **Models** (`models.py`): Contêm métodos de negócio relacionados aos dados
- **Services** (`services/`): Lógica de negócio complexa
- **Views** (`views.py`): Apenas manipulação HTTP
- **Core** (`core/`): Constantes, exceções e utilitários compartilhados

### Princípios Aplicados

- ✅ **Single Responsibility**: Cada classe/função tem uma única responsabilidade
- ✅ **DRY (Don't Repeat Yourself)**: Código reutilizável em utils
- ✅ **Separation of Concerns**: Views, Services e Models separados
- ✅ **Nomes Descritivos**: Funções e variáveis com nomes claros
- ✅ **Funções Pequenas**: Funções focadas e fáceis de entender
- ✅ **Tratamento de Erros**: Exceções específicas por domínio

### Fluxo de Dados

```
HTTP Request → View → Service → Model → Database
                ↓
            Serializer
                ↓
         HTTP Response
```

## 📝 Modelos de Dados

### Plano
- `nome_plano`: Nome do plano
- `valor_base`: Valor mensal
- `periodicidade_meses`: Periodicidade (1 = mensal, 3 = trimestral, etc.)
- `ativo`: Se o plano está ativo

### Cliente
- `plano`: Plano associado (ForeignKey)
- `nome`: Nome completo
- `cpf`: CPF (único)
- `telefone_whatsapp`: Telefone para WhatsApp
- `email`: E-mail
- `data_inicio_contrato`: Data de início
- `status_cliente`: ATIVO, INATIVO_ATRASO, INATIVO_MANUAL

### Cobrança
- `cliente`: Cliente associado (ForeignKey)
- `valor_base`: Valor base
- `valor_multa_juros`: Multa e juros
- `valor_total_devido`: Valor total
- `data_vencimento`: Data de vencimento
- `data_pagamento`: Data de pagamento (opcional)
- `referencia_ciclo`: Referência (ex: "2025-12")
- `status_cobranca`: PENDENTE, PAGO, ATRASADO, CANCELADO

### Notificação
- `cobranca`: Cobrança associada (ForeignKey)
- `tipo_regua`: Tipo (D-3, D+1, D+10, etc.)
- `tipo_canal`: EMAIL ou WHATSAPP
- `conteudo_mensagem`: Conteúdo enviado
- `data_agendada`: Data agendada
- `data_envio_real`: Data real de envio
- `status_envio`: AGENDADO, ENVIADO, FALHA

## 🔒 Segurança

⚠️ **IMPORTANTE**: Este projeto está configurado para **desenvolvimento**. Para produção:

1. Altere `DEBUG = False` em `settings.py`
2. Configure `ALLOWED_HOSTS` com domínios específicos
3. Use variáveis de ambiente para credenciais sensíveis
4. Configure autenticação na API (JWT, OAuth2, etc.)
5. Use HTTPS
6. Configure um banco de dados de produção (PostgreSQL, MySQL)

## 📞 Suporte

Para dúvidas ou problemas, verifique:
- Logs do Django: `python manage.py runserver` mostra erros
- Logs do agendador: `python manage.py startjobs` mostra execuções
- Tabela `Notificacao`: Registra todas as tentativas de envio

## 📄 Licença

Este projeto é privado e de uso interno.

---

**Desenvolvido seguindo princípios de Clean Code e boas práticas de desenvolvimento.**



