from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Sum
from django.core.mail import send_mail
from django.conf import settings
from .models import FluxoAgua, ControleFluxo, MetaConsumo, EmailNotification


@receiver(post_save, sender=FluxoAgua)
def verificar_consumo_e_controlar_fluxo(sender, instance, created, **kwargs):
    """
    Signal que verifica o consumo diário após cada registro de FluxoAgua.
    Se o consumo ultrapassar a meta e o desligamento automático ainda não ocorreu hoje,
    desliga o fluxo automaticamente.
    """
    if not created:
        return

    hoje = timezone.localdate()

    # Busca a meta atual (usando o método singleton)
    meta = MetaConsumo.get_meta_atual()
    if not meta:
        return  # Se não há meta configurada, não faz nada

    # Calcula o consumo total do dia
    consumo_hoje = FluxoAgua.objects.filter(
        data_hora__date=hoje
    ).aggregate(total=Sum('valor_diferenca'))['total'] or Decimal('0.00')

    # Busca ou cria o controle de fluxo do dia
    # IMPORTANTE: Cada dia é independente. Defaults reseta todas as flags para um novo dia.
    controle, created_controle = ControleFluxo.objects.get_or_create(
        data=hoje,
        defaults={
            'status': 'on',
            'desligamento_automatico_ocorreu': False,
            'usuario_alterou_manualmente': False,
            'email_enviado_hoje': False
        }
    )

    # Se foi criado agora (novo dia), todas as flags começam zeradas
    # O controle de ontem (se existir) não afeta o de hoje

    # Verifica se deve desligar automaticamente
    if consumo_hoje >= meta.meta_diaria_litros:
        # Só desliga se ainda não desligou automaticamente hoje
        # E se o usuário não alterou manualmente HOJE
        if not controle.desligamento_automatico_ocorreu and not controle.usuario_alterou_manualmente:
            controle.status = 'off'
            controle.desligamento_automatico_ocorreu = True
            controle.save()

        # Envia email de notificação se ainda não enviou HOJE
        # Esta verificação garante que mesmo com várias leituras ultrapassando a meta,
        # o email será enviado apenas uma vez por dia
        if not controle.email_enviado_hoje:
            enviar_notificacao_email(consumo_hoje, meta.meta_diaria_litros, hoje)
            controle.email_enviado_hoje = True
            controle.save()


def enviar_notificacao_email(consumo_atual, meta_diaria, data):
    """
    Envia email de notificação quando o consumo ultrapassa a meta.
    Envia apenas uma vez por dia.
    """
    # Busca todos os emails ativos
    emails_ativos = EmailNotification.objects.filter(ativo=True).values_list('email', flat=True)

    if not emails_ativos:
        return  # Não há emails cadastrados

    # Monta o assunto e corpo do email
    assunto = f"⚠️ Alerta: Meta de Consumo de Água Ultrapassada - {data.strftime('%d/%m/%Y')}"

    corpo = f"""
    Olá,

    Este é um alerta automático do Sistema de Controle de Fluxo de Água.

    📊 RESUMO DO CONSUMO:

    • Data: {data.strftime('%d/%m/%Y')}
    • Meta Diária: {meta_diaria} litros
    • Consumo Atual: {consumo_atual} litros
    • Excedente: {consumo_atual - meta_diaria} litros ({((consumo_atual - meta_diaria) / meta_diaria * 100):.1f}%)

    ⚠️ O consumo de água ultrapassou a meta diária estabelecida.
    O fluxo de água foi automaticamente DESLIGADO para evitar desperdício.

    🔧 AÇÕES DISPONÍVEIS:
    • Você pode reativar manualmente o fluxo através do painel de controle
    • Acesse: https://fluxo-agua.kauan.space/docs/swagger/
    • Endpoint: PATCH /controle-fluxo/alterar_status/

    💡 DICAS PARA ECONOMIA:
    • Verifique possíveis vazamentos
    • Revise o uso de água durante o dia
    • Considere ajustar a meta diária se necessário

    ---
    Esta é uma mensagem automática. Não responda a este email.
    Sistema de Controle de Fluxo de Água
    """

    try:
        send_mail(
            subject=assunto,
            message=corpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=list(emails_ativos),
            fail_silently=False,
        )
        print(f"✅ Email de alerta enviado para {len(emails_ativos)} destinatário(s)")
    except Exception as e:
        print(f"❌ Erro ao enviar email: {str(e)}")
