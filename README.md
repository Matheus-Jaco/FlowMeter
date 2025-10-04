# API de Controle de Fluxo de Água

Esta API permite o monitoramento, controle e gestão do consumo de água em residências ou estabelecimentos, promovendo o uso consciente da água e evitando desperdícios.

## Funcionalidades

- Cadastro e gerenciamento de sensores de fluxo de água
- Registro e consulta de leituras de consumo
- Definição de metas diárias de consumo
- Monitoramento do consumo diário e mensal
- Controle automático ou manual do fluxo de água (ligar/desligar)
- Notificações por e-mail quando o consumo ultrapassar a meta

<img width="1900" height="1060" alt="Captura de tela 2025-10-04 181926" src="https://github.com/user-attachments/assets/529c6434-feb0-40bf-a208-94f442f31e38" />


## Principais Endpoints

- `/sensores/` — Gerenciamento de sensores
- `/fluxo/` — Leituras de fluxo de água
- `/meta-consumo/` — Definição e consulta de metas
- `/controle-fluxo/` — Controle do fluxo (on/off)
- `/consumo-diario/` e `/consumo-mensal/` — Relatórios de consumo
- `/emails-notificacao/` — Cadastro de e-mails para alertas
- 
## Como rodar localmente

1. **Clone o repositório**
    ```sh
    git clone <url-do-repositorio>
    cd fluxo-agua-main
    ```

2. **Crie e ative um ambiente virtual**
    ```sh
    python -m venv .venv
    .venv\Scripts\activate
    ```

3. **Instale as dependências**
    ```sh
    pip install -r requirements.txt
    ```

4. **Configure as variáveis de ambiente**
    - Renomeie `.env.production` para `.env` e ajuste as variáveis conforme seu ambiente local.

5. **Aplique as migrações**
    ```sh
    python manage.py migrate
    ```

6. **Crie um superusuário (opcional)**
    ```sh
    python manage.py createsuperuser
    ```

7. **Inicie o servidor**
    ```sh
    python manage.py runserver
    ```

8. **Acesse a API**
    - [http://localhost:8000/](http://localhost:8000/)
    - [http://localhost:8000/docs/swagger/](http://localhost:8000/docs/swagger/)

## Configuração de E-mail

Para envio de notificações por e-mail, configure as variáveis no arquivo `.env`:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app-do-gmail
DEFAULT_FROM_EMAIL=Sistema de Controle de Água <seu-email@gmail.com>
```

> **Atenção:** Use uma senha de app do Gmail para maior segurança.

<img width="1900" height="1060" alt="Captura de tela 2025-10-04 183606" src="https://github.com/user-attachments/assets/904f9ecb-9b12-403e-9d6d-636e80b8fe49" />


## Banco de Dados

Por padrão, o projeto utiliza PostgreSQL.  
Altere a variável `DATABASE_URL` no `.env` conforme seu ambiente:

```env
DATABASE_URL=postgresql://usuario:senha@localhost:5432/nome_do_banco
```

## Licença

MIT License

---

Desenvolvido por Matheus-Jaco.
