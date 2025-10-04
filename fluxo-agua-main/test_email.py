"""
Script para testar envio de email no Django

Uso:
    python test_email.py

Ou via Django shell:
    python manage.py shell < test_email.py
"""

import os
import django

# Configura o Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "setup.settings")
django.setup()

from django.conf import settings
from django.core.mail import send_mail


def test_email_simples():
    """Teste simples de envio de email"""
    print("\n" + "=" * 60)
    print("TESTE 1: Envio Simples de Email")
    print("=" * 60)

    print("\nConfigurações:")
    print(f"  Backend: {settings.EMAIL_BACKEND}")
    print(f"  Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
    print(f"  TLS: {settings.EMAIL_USE_TLS}")
    print(f"  De: {settings.DEFAULT_FROM_EMAIL}")
    print(f"  Usuário: {settings.EMAIL_HOST_USER}")

    destinatario = input("\nDigite o email de destino para teste: ").strip()

    if not destinatario:
        print("Email não informado. Teste cancelado.")
        return

    try:
        print(f"\nEnviando email de teste para {destinatario}...")

        resultado = send_mail(
            subject="Teste - Sistema de Controle de Fluxo de Água",
            message="""
            Olá!

            Este é um email de teste do Sistema de Controle de Fluxo de Água.

            Se você recebeu este email, significa que a configuração SMTP está funcionando corretamente!

            Detalhes do sistema:
            - Servidor: Django Email System
            - Data/Hora: Agora mesmo
            - Status: Funcionando

            ---
            Esta é uma mensagem de teste automática.
            Sistema de Controle de Fluxo de Água
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destinatario],
            fail_silently=False,
        )

        if resultado == 1:
            print("\nEmail enviado com sucesso!")
            print(f"   Verifique a caixa de entrada de: {destinatario}")
        else:
            print("\nEmail pode não ter sido enviado. Verifique as configurações.")

    except Exception as e:
        print(f"\nErro ao enviar email:")
        print(f"   {type(e).__name__}: {str(e)}")
        print("\nPossíveis soluções:")
        print("   1. Verifique se EMAIL_HOST_USER e EMAIL_HOST_PASSWORD estão corretos")
        print(
            "   2. Para Gmail, use uma 'Senha de App': https://myaccount.google.com/apppasswords"
        )
        print("   3. Verifique se EMAIL_HOST e EMAIL_PORT estão corretos")
        print("   4. Confira se o firewall permite conexões na porta 587")


def test_email_notificacao_meta():
    """Testa o email de notificação quando meta é ultrapassada"""
    print("\n" + "=" * 60)
    print("TESTE 2: Email de Notificação de Meta Ultrapassada")
    print("=" * 60)

    from datetime import date
    from decimal import Decimal

    destinatario = input("\nDigite o email de destino para teste: ").strip()

    if not destinatario:
        print("Email não informado. Teste cancelado.")
        return

    # Simula dados
    consumo_atual = Decimal("1500.50")
    meta_diaria = Decimal("1000.00")
    data_teste = date.today()

    assunto = f"Alerta: Meta de Consumo de Água Ultrapassada - {data_teste.strftime('%d/%m/%Y')}"

    corpo = f"""
    Olá,

    Este é um alerta automático do Sistema de Controle de Fluxo de Água.

    RESUMO DO CONSUMO:

    • Data: {data_teste.strftime("%d/%m/%Y")}
    • Meta Diária: {meta_diaria} litros
    • Consumo Atual: {consumo_atual} litros
    • Excedente: {consumo_atual - meta_diaria} litros ({((consumo_atual - meta_diaria) / meta_diaria * 100):.1f}%)

    O consumo de água ultrapassou a meta diária estabelecida.
    O fluxo de água foi automaticamente DESLIGADO para evitar desperdício.

    AÇÕES DISPONÍVEIS:
    • Você pode reativar manualmente o fluxo através do painel de controle
    • Acesse: https://fluxo-agua.kauan.space/docs/swagger/
    • Endpoint: PATCH /controle-fluxo/alterar_status/

    DICAS PARA ECONOMIA:
    • Verifique possíveis vazamentos
    • Revise o uso de água durante o dia
    • Considere ajustar a meta diária se necessário

    ---
    Esta é uma mensagem de teste. Não responda a este email.
    Sistema de Controle de Fluxo de Água
    """

    try:
        print(f"\nEnviando email de notificação para {destinatario}...")

        resultado = send_mail(
            subject=assunto,
            message=corpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destinatario],
            fail_silently=False,
        )

        if resultado == 1:
            print("\nEmail de notificação enviado com sucesso!")
            print(f"   Verifique a caixa de entrada de: {destinatario}")
        else:
            print("\nEmail pode não ter sido enviado.")

    except Exception as e:
        print(f"\nErro ao enviar email:")
        print(f"   {type(e).__name__}: {str(e)}")


def test_multiplos_destinatarios():
    """Testa envio para múltiplos destinatários"""
    print("\n" + "=" * 60)
    print("TESTE 3: Envio para Múltiplos Destinatários")
    print("=" * 60)

    print("\nDigite os emails de destino separados por vírgula:")
    emails_input = input(
        "   Exemplo: email1@example.com, email2@example.com\n   > "
    ).strip()

    if not emails_input:
        print("Nenhum email informado. Teste cancelado.")
        return

    destinatarios = [email.strip() for email in emails_input.split(",")]

    print(f"\nDestinatários ({len(destinatarios)}):")
    for i, email in enumerate(destinatarios, 1):
        print(f"   {i}. {email}")

    try:
        print(f"\nEnviando emails...")

        resultado = send_mail(
            subject="Teste Múltiplos Destinatários - Sistema de Controle de Água",
            message="""
            Olá!

            Este é um teste de envio para múltiplos destinatários do Sistema de Controle de Fluxo de Água.

            Você está recebendo este email porque seu endereço foi cadastrado para receber notificações
            quando o consumo de água ultrapassar a meta diária estabelecida.

            Configuração funcionando corretamente!

            ---
            Esta é uma mensagem de teste automática.
            Sistema de Controle de Fluxo de Água
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=destinatarios,
            fail_silently=False,
        )

        if resultado == 1:
            print(
                f"\nEmails enviados com sucesso para {len(destinatarios)} destinatário(s)!"
            )
        else:
            print("\nAlguns emails podem não ter sido enviados.")

    except Exception as e:
        print(f"\nErro ao enviar emails:")
        print(f"   {type(e).__name__}: {str(e)}")


def menu():
    """Menu principal"""
    while True:
        print("\n" + "=" * 60)
        print("TESTE DE ENVIO DE EMAIL - Django")
        print("=" * 60)
        print("\nEscolha o teste:")
        print("  1. Teste simples de email")
        print("  2. Teste email de notificação (meta ultrapassada)")
        print("  3. Teste múltiplos destinatários")
        print("  0. Sair")

        escolha = input("\nDigite sua escolha: ").strip()

        if escolha == "1":
            test_email_simples()
        elif escolha == "2":
            test_email_notificacao_meta()
        elif escolha == "3":
            test_multiplos_destinatarios()
        elif escolha == "0":
            print("\nAté logo!")
            break
        else:
            print("\nOpção inválida. Tente novamente.")


if __name__ == "__main__":
    menu()
