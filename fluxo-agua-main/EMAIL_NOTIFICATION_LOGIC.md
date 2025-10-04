# Lógica de Notificação por Email

## 📧 Funcionamento do Sistema de Emails

### Como funciona:

1. **Cadastro de Emails**
   - Emails são cadastrados no endpoint `/emails-notificacao/`
   - Cada email tem um status `ativo` (True/False)
   - Apenas emails ativos recebem notificações

2. **Quando o Email é Enviado**
   - ✅ Quando o consumo diário ultrapassa a meta configurada
   - ✅ Apenas **UMA VEZ POR DIA**
   - ✅ Para **TODOS** os emails ativos cadastrados

3. **Isolamento por Dia**
   - ✅ Cada dia tem seu próprio registro de controle (`ControleFluxo`)
   - ✅ O que aconteceu ontem **NÃO afeta** hoje
   - ✅ Flags são resetadas automaticamente no novo dia

### ✅ Flags de Controle Diário - Isolamento Garantido:

Cada dia cria um **novo registro** com chave única por data.

**Todas as 4 flags são resetadas automaticamente no novo dia:**

```python
# Registro de ONTEM (permanece no banco mas NÃO afeta hoje)
ControleFluxo (01/10):
  - data: 2025-10-01
  - status: 'off'
  - desligamento_automatico_ocorreu: True
  - usuario_alterou_manualmente: True
  - email_enviado_hoje: True

# Registro de HOJE (novo, todas flags zeradas!)
ControleFluxo (02/10):
  - data: 2025-10-02  ← Nova chave única
  - status: 'on'  ← RESETADO
  - desligamento_automatico_ocorreu: False  ← RESETADO
  - usuario_alterou_manualmente: False  ← RESETADO
  - email_enviado_hoje: False  ← RESETADO
```

**Isolamento via `get_or_create(data=hoje)`:**
- Sempre busca/cria usando `data = hoje`
- `defaults` só aplicado quando cria NOVO registro
- Ontem fica salvo mas não interfere em nada

### Cenários de Teste:

#### ✅ Cenário 1: Novo Dia - Tudo Reseta
**Situação:**
- Dia 01: Consumo ultrapassou meta, fluxo off, email enviado, usuário reativou
- Dia 02: Primeiro registro do dia

**Resultado:**
- ✅ Novo registro criado com todas flags zeradas
- ✅ Status volta para 'on' automaticamente
- ✅ Sistema pode desligar novamente se ultrapassar meta
- ✅ Email pode ser enviado novamente

#### ✅ Cenário 2: Múltiplas Leituras no Mesmo Dia
**Situação:**
- Leitura 1: Consumo = 800L (meta 1000L) → Nada acontece
- Leitura 2: Consumo = 1100L (ultrapassou!) → Desliga + Email
- Leitura 3: Consumo = 1200L (ainda ultrapassado)

**Resultado:**
- ✅ Email enviado apenas na Leitura 2
- ✅ Leitura 3 não envia email novamente

#### ✅ Cenário 3: Usuário Reativa Após Desligamento
**Situação:**
- Consumo ultrapassou meta → Sistema desliga + Email
- Usuário reativa manualmente para 'on'
- Mais consumo é registrado

**Resultado:**
- ✅ Status permanece 'on' (decisão do usuário prevalece)
- ✅ Sistema não desliga novamente hoje
- ✅ Email não é enviado novamente (já foi enviado hoje)

### Endpoints de Email:

```bash
# Listar todos os emails
GET /emails-notificacao/

# Cadastrar novo email
POST /emails-notificacao/
{
  "email": "usuario@example.com",
  "ativo": true
}

# Atualizar email
PATCH /emails-notificacao/{id}/
{
  "ativo": false
}

# Ativar/Desativar rapidamente
PATCH /emails-notificacao/{id}/toggle_ativo/
{
  "ativo": true
}

# Deletar email
DELETE /emails-notificacao/{id}/
```

### Configuração SMTP:

No arquivo `.env` ou variáveis de ambiente:

```bash
# Gmail Example
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app
DEFAULT_FROM_EMAIL=Sistema de Controle de Água <seu-email@gmail.com>
```

### Como Gerar Senha de App do Gmail:

1. Acesse: https://myaccount.google.com/apppasswords
2. Crie uma senha de app para "Mail"
3. Use essa senha no `EMAIL_HOST_PASSWORD`

### Logs:

O sistema exibe logs no console:
- ✅ `Email de alerta enviado para X destinatário(s)`
- ❌ `Erro ao enviar email: [detalhes do erro]`

### Testar Envio de Email:

```python
# No shell do Django
python manage.py shell

from django.core.mail import send_mail
send_mail(
    'Teste',
    'Mensagem de teste',
    'seu-email@gmail.com',
    ['destinatario@example.com'],
)
```
