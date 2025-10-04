from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.timezone import make_aware
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import FluxoAgua, Sensor, ConsumoDiario, MetaConsumo, ControleFluxo, EmailNotification
from .serializers import FluxoAguaSerializer, SensorSerializer, MetaConsumoSerializer, ControleFluxoSerializer, EmailNotificationSerializer


class SensorViewSet(ModelViewSet):
    queryset = Sensor.objects.all()
    serializer_class = SensorSerializer


class FluxoViewSet(ModelViewSet):
    serializer_class = FluxoAguaSerializer
    queryset = FluxoAgua.objects.all().order_by("-id")
    

    def create(self, request, *args, **kwargs):
        sensor_id = request.data.get("sensor")
        valor_str = request.data.get("valor")

        # Trata string convertendo vírgula para ponto se necessário
        if isinstance(valor_str, str):
            valor_str = valor_str.strip().replace(',', '.')

        valor_recebido = Decimal(valor_str)

        # Busca última leitura do sensor
        ultima_leitura = (
            FluxoAgua.objects.filter(sensor_id=sensor_id).order_by("-id").first()
        )

        valor_diferenca = None

        if ultima_leitura:
            ultimo_valor = ultima_leitura.valor
            
            if valor_recebido < ultimo_valor:
                valor_diferenca = valor_recebido
            else:
                valor_diferenca = valor_recebido - ultimo_valor
        else:
            # Primeira leitura do sensor → diferença será o próprio valor
            valor_diferenca = valor_recebido

        # Cria o registro com o valor original e a diferença
        data_para_salvar = request.data.copy()
        data_para_salvar["valor"] = valor_recebido
        data_para_salvar["valor_diferenca"] = valor_diferenca

        serializer = self.get_serializer(data=data_para_salvar)
        serializer.is_valid(raise_exception=True)
        fluxo = serializer.save()

        # Garante que a data_hora seja timezone-aware
        if timezone.is_naive(fluxo.data_hora):
            fluxo.data_hora = make_aware(fluxo.data_hora)
            fluxo.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def reset_database(self, request):
        """
        Endpoint para resetar completamente o banco de dados
        Requer confirmação via parâmetro 'confirm': true
        """
        if not request.data.get('confirm'):
            return Response(
                {
                    "error": "Operação requer confirmação",
                    "message": "Envie 'confirm': true para confirmar o reset do banco",
                    "warning": "Esta operação irá deletar TODOS os dados!"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                # Conta registros antes de deletar
                deleted_fluxo = FluxoAgua.objects.all().count()
                deleted_consumo = ConsumoDiario.objects.all().count()
                deleted_sensor = Sensor.objects.all().count()

                # Deleta todos os registros
                FluxoAgua.objects.all().delete()
                ConsumoDiario.objects.all().delete()
                Sensor.objects.all().delete()

                return Response({
                    "success": True,
                    "message": "Banco de dados resetado com sucesso!",
                    "deleted_records": {
                        "fluxo_agua": deleted_fluxo,
                        "consumo_diario": deleted_consumo,
                        "sensores": deleted_sensor
                    }
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {
                    "error": "Erro ao resetar banco de dados",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConsumoResidenciaView(ViewSet):
    """
    Retorna consumo diário e total da residência
    """

    def list(self, request):
        hoje = timezone.localdate()
        # Consulta todas as leituras do dia
        leituras = FluxoAgua.objects.filter(data_hora__date=hoje)

        # Agrega consumo por sensor
        consumo_por_sensor = leituras.values("sensor__nome").annotate(
            consumo_total=Sum("valor_diferenca")
        )

        # Formata a resposta
        resposta = [
            {"sensor": c["sensor__nome"], "consumo": f"{c['consumo_total']:.2f}"}
            for c in consumo_por_sensor
        ]

        total_residencia = leituras.aggregate(total=Sum("valor_diferenca"))["total"] or Decimal(
            "0.00"
        )

        return Response(
            {
                "data": hoje.strftime("%d/%m/%Y"),
                "sensores": resposta,
                "total_residencia": f"{total_residencia:.2f}",
            }
        )


class ConsumoMensalView(ViewSet):
    """
    Retorna consumo mensal da residência

    - **GET /consumo-mensal/**: Retorna consumo de todos os meses do ano atual
    - **GET /consumo-mensal/?mes=X**: Retorna consumo detalhado do mês X do ano atual (1-12)
    """

    @swagger_auto_schema(
        operation_description="Retorna consumo mensal. Sem parâmetros retorna todos os meses do ano atual. Com parâmetro 'mes' retorna detalhes do mês específico.",
        manual_parameters=[
            openapi.Parameter(
                'mes',
                openapi.IN_QUERY,
                description="Mês específico para consultar (1-12). Se não informado, retorna todos os meses do ano atual.",
                type=openapi.TYPE_INTEGER,
                required=False,
                minimum=1,
                maximum=12
            )
        ],
        responses={
            200: openapi.Response(
                description="Consumo mensal retornado com sucesso",
                examples={
                    "application/json": {
                        "ano": 2025,
                        "meses": [
                            {
                                "mes": 1,
                                "nome_mes": "Janeiro",
                                "consumo_total": "15000.50"
                            },
                            {
                                "mes": 2,
                                "nome_mes": "Fevereiro",
                                "consumo_total": "12500.75"
                            }
                        ],
                        "total_ano": "27501.25"
                    }
                }
            )
        }
    )
    def list(self, request):
        hoje = timezone.localdate()
        ano_atual = hoje.year
        mes_param = request.query_params.get('mes')

        # Se foi passado um mês específico, retorna detalhes daquele mês
        if mes_param:
            try:
                mes = int(mes_param)
                if mes < 1 or mes > 12:
                    return Response(
                        {"error": "Mês deve estar entre 1 e 12"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except ValueError:
                return Response(
                    {"error": "Mês deve ser um número inteiro"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            leituras = FluxoAgua.objects.filter(data_hora__year=ano_atual, data_hora__month=mes)

            # Agrupa consumo por dia e sensor
            consumo_por_dia = leituras.values("data_hora__date", "sensor__nome").annotate(
                consumo_total=Sum("valor_diferenca")
            )

            resposta_dias = [
                {
                    "data": c["data_hora__date"].strftime("%d/%m/%Y"),
                    "sensor": c["sensor__nome"],
                    "consumo_total": f"{c['consumo_total']:.2f}",
                }
                for c in consumo_por_dia
            ]

            total_mes = leituras.aggregate(total=Sum("valor_diferenca"))["total"] or Decimal("0.00")

            # Nomes dos meses em português
            meses_nomes = [
                "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
            ]

            return Response(
                {
                    "ano": ano_atual,
                    "mes": mes,
                    "nome_mes": meses_nomes[mes - 1],
                    "consumo_por_dia": resposta_dias,
                    "total_mes": f"{total_mes:.2f}",
                }
            )

        # Caso contrário, retorna todos os meses do ano atual
        leituras_ano = FluxoAgua.objects.filter(data_hora__year=ano_atual)

        # Agrupa consumo por mês
        consumo_por_mes = leituras_ano.values("data_hora__month").annotate(
            consumo_total=Sum("valor_diferenca")
        ).order_by("data_hora__month")

        # Cria um dicionário com o consumo de cada mês
        meses_consumo = {c["data_hora__month"]: c["consumo_total"] for c in consumo_por_mes}

        # Nomes dos meses em português
        meses_nomes = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]

        # Monta resposta com todos os 12 meses (mesmo que alguns tenham consumo zero)
        meses_resposta = [
            {
                "mes": i + 1,
                "nome_mes": meses_nomes[i],
                "consumo_total": f"{meses_consumo.get(i + 1, Decimal('0.00')):.2f}"
            }
            for i in range(12)
        ]

        total_ano = leituras_ano.aggregate(total=Sum("valor_diferenca"))["total"] or Decimal("0.00")

        return Response(
            {
                "ano": ano_atual,
                "meses": meses_resposta,
                "total_ano": f"{total_ano:.2f}",
            }
        )


class MetaConsumoViewSet(ViewSet):
    """
    Gerenciamento da Meta de Consumo da Residência (Singleton)

    Apenas uma meta pode existir no sistema. Não é necessário passar ID como parâmetro.

    - **GET /meta-consumo/**: Retorna a meta atual (cria uma padrão se não existir)
    - **POST /meta-consumo/**: Cria a primeira meta (apenas se não existir)
    - **PUT/PATCH /meta-consumo/**: Atualiza a meta existente
    """

    @swagger_auto_schema(
        operation_description="Retorna a meta de consumo atual da residência",
        responses={
            200: openapi.Response(
                description="Meta retornada com sucesso",
                schema=MetaConsumoSerializer,
                examples={
                    "application/json": {
                        "id": 1,
                        "meta_diaria_litros": "1000.00",
                        "data_criacao": "2025-10-02T10:00:00Z",
                        "data_atualizacao": "2025-10-02T10:00:00Z"
                    }
                }
            )
        }
    )
    def list(self, request):
        """Retorna a meta atual"""
        meta = MetaConsumo.get_meta_atual()
        if not meta:
            return Response(
                {"message": "Nenhuma meta configurada"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = MetaConsumoSerializer(meta)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Cria a primeira meta de consumo (apenas se não existir)",
        request_body=MetaConsumoSerializer,
        responses={
            201: MetaConsumoSerializer,
            400: openapi.Response(
                description="Já existe uma meta cadastrada",
                examples={
                    "application/json": {
                        "error": "Já existe uma meta cadastrada. Use PUT/PATCH para atualizar."
                    }
                }
            )
        }
    )
    def create(self, request):
        """Cria a primeira meta"""
        if MetaConsumo.objects.exists():
            return Response(
                {"error": "Já existe uma meta cadastrada. Use PUT/PATCH para atualizar."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = MetaConsumoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        methods=['put', 'patch'],
        operation_description="Atualiza a meta de consumo existente",
        request_body=MetaConsumoSerializer,
        responses={
            200: MetaConsumoSerializer,
            404: openapi.Response(
                description="Nenhuma meta encontrada",
                examples={
                    "application/json": {
                        "error": "Nenhuma meta configurada. Use POST para criar."
                    }
                }
            )
        }
    )
    @action(detail=False, methods=['put', 'patch'])
    def atualizar(self, request):
        """Atualiza a meta existente"""
        meta = MetaConsumo.get_meta_atual()
        if not meta:
            return Response(
                {"error": "Nenhuma meta configurada. Use POST para criar."},
                status=status.HTTP_404_NOT_FOUND
            )

        partial = request.method == 'PATCH'
        serializer = MetaConsumoSerializer(meta, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ControleFluxoViewSet(ViewSet):
    """
    Gerencia o status do fluxo de água (on/off)

    ## Funcionalidades:
    - **GET /controle-fluxo/**: Retorna o status atual do fluxo de hoje
    - **PATCH /controle-fluxo/alterar_status/**: Permite alteração manual do status

    ## Lógica de controle:
    1. O sistema desliga automaticamente quando o consumo ultrapassa a meta (apenas 1x por dia)
    2. O usuário pode reativar manualmente mesmo após desligamento automático
    3. A decisão manual do usuário prevalece até o fim do dia
    4. No dia seguinte, a lógica é resetada
    """

    @swagger_auto_schema(
        operation_description="Retorna o status atual do fluxo de água",
        responses={
            200: openapi.Response(
                description="Status do fluxo retornado com sucesso",
                schema=ControleFluxoSerializer,
                examples={
                    "application/json": {
                        "data": "2025-10-02",
                        "status": "on",
                        "desligamento_automatico_ocorreu": False,
                        "usuario_alterou_manualmente": False,
                        "data_hora_atualizacao": "2025-10-02T10:30:00Z"
                    }
                }
            )
        }
    )
    def list(self, request):
        """Retorna o status do fluxo de hoje"""
        hoje = timezone.localdate()
        controle, created = ControleFluxo.objects.get_or_create(
            data=hoje,
            defaults={
                'status': 'on',
                'desligamento_automatico_ocorreu': False,
                'usuario_alterou_manualmente': False,
                'email_enviado_hoje': False
            }
        )
        serializer = ControleFluxoSerializer(controle)
        return Response(serializer.data)

    @swagger_auto_schema(
        methods=['patch'],
        operation_description="Permite ao usuário alterar manualmente o status do fluxo",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['status'],
            properties={
                'status': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['on', 'off'],
                    description='Novo status do fluxo: "on" para ligar, "off" para desligar'
                )
            },
            example={'status': 'on'}
        ),
        responses={
            200: ControleFluxoSerializer,
            400: openapi.Response(
                description="Erro de validação",
                examples={
                    "application/json": {
                        "error": "Status deve ser \"on\" ou \"off\""
                    }
                }
            )
        }
    )
    @action(detail=False, methods=['patch'])
    def alterar_status(self, request):
        """Permite ao usuário alterar manualmente o status"""
        hoje = timezone.localdate()
        novo_status = request.data.get('status')

        if novo_status not in ['on', 'off']:
            return Response(
                {'error': 'Status deve ser "on" ou "off"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        controle, created = ControleFluxo.objects.get_or_create(
            data=hoje,
            defaults={
                'status': 'on',
                'desligamento_automatico_ocorreu': False,
                'usuario_alterou_manualmente': False,
                'email_enviado_hoje': False
            }
        )

        controle.status = novo_status
        controle.usuario_alterou_manualmente = True
        controle.save()

        serializer = ControleFluxoSerializer(controle)
        return Response(serializer.data)


class EmailNotificationViewSet(ModelViewSet):
    """
    CRUD completo para Emails de Notificação

    Gerencia os emails que receberão alertas quando o consumo ultrapassar a meta.

    - **GET /emails-notificacao/**: Lista todos os emails cadastrados
    - **POST /emails-notificacao/**: Cadastra um novo email
    - **GET /emails-notificacao/{id}/**: Retorna detalhes de um email
    - **PUT/PATCH /emails-notificacao/{id}/**: Atualiza um email
    - **DELETE /emails-notificacao/{id}/**: Remove um email
    """
    queryset = EmailNotification.objects.all()
    serializer_class = EmailNotificationSerializer

    @swagger_auto_schema(
        operation_description="Lista todos os emails cadastrados para receber notificações",
        responses={
            200: EmailNotificationSerializer(many=True)
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Cadastra um novo email para receber notificações de consumo",
        request_body=EmailNotificationSerializer,
        responses={
            201: EmailNotificationSerializer,
            400: openapi.Response(
                description="Erro de validação",
                examples={
                    "application/json": {
                        "email": ["Este campo é obrigatório."]
                    }
                }
            )
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        methods=['patch'],
        operation_description="Ativa ou desativa um email de notificação",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'ativo': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Status do email (true=ativo, false=inativo)'
                )
            }
        ),
        responses={
            200: EmailNotificationSerializer
        }
    )
    @action(detail=True, methods=['patch'])
    def toggle_ativo(self, request, pk=None):
        """Ativa ou desativa um email de notificação"""
        email_notif = self.get_object()
        ativo = request.data.get('ativo')

        if ativo is None:
            return Response(
                {"error": "Campo 'ativo' é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST
            )

        email_notif.ativo = ativo
        email_notif.save()

        serializer = self.get_serializer(email_notif)
        return Response(serializer.data)
    